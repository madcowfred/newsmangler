# Copyright (c) 2005-2012 freddie@wafflemonster.org
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"A basic NNTP client using asyncore"

import asyncore
import errno
import logging
import re
import select
import socket
import time

# ---------------------------------------------------------------------------

STATE_DISCONNECTED = 0
STATE_CONNECTING = 1
STATE_CONNECTED = 2

MODE_AUTH = 0
MODE_COMMAND = 1
MODE_POST_INIT = 2
MODE_POST_DATA = 3
MODE_POST_DONE = 4
MODE_DATA = 5

POST_BUFFER_MIN = 16384
POST_READ_SIZE = 262144

MSGID_RE = re.compile(r'(<\S+@\S+>)')

# ---------------------------------------------------------------------------

class asyncNNTP(asyncore.dispatcher):
    def __init__(self, parent, connid, host, port, bindto, username, password):
        asyncore.dispatcher.__init__(self)
        
        self.logger = logging.getLogger('mangler')
        
        self.parent = parent
        self.connid = connid
        self.host = host
        self.port = port
        self.bindto = bindto
        self.username = username
        self.password = password
        
        self.reset()
    
    def reset(self):
        self._readbuf = ''
        self._writebuf = ''
        self._article = None
        self._pointer = 0
        
        self.reconnect_at = 0
        self.mode = MODE_AUTH
        self.state = STATE_DISCONNECTED

    def do_connect(self):
        # Create the socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Try to set our send buffer a bit larger
        for i in range(17, 13, -1):
            try:
                self.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2**i)
            except socket.error:
                continue
            else:
                break
        self.logger.debug('%d: SO_SNDBUF is %s', self.connid, self.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
        
        # If we have to bind our socket to an IP, do that
        #if self.bindto is not None:
        #    self.bind((self.bindto, 0))
        
        # Try to connect. This can blow up!
        try:
            self.connect((self.host, self.port))
        except (socket.error, socket.gaierror), msg:
            self.really_close(msg)
        else:
            self.state = STATE_CONNECTING
            self.logger.debug('%d: connecting to %s:%s', self.connid, self.host, self.port)
    
    # -----------------------------------------------------------------------
    # Check to see if it's time to reconnect yet
    def reconnect_check(self, now):
    	if self.state == STATE_DISCONNECTED and now >= self.reconnect_at:
        	self.do_connect()

    def add_channel(self, map=None):
        self.logger.debug('%d: adding FD %d to poller', self.connid, self._fileno)
        
        asyncore.dispatcher.add_channel(self, map)

        # Add ourselves to the poll object
        asyncore.poller.register(self._fileno)
    
    def del_channel(self, map=None):
        self.logger.debug('%d: removing FD %d from poller', self.connid, self._fileno)

        # Remove ourselves from the async map
        asyncore.dispatcher.del_channel(self, map)
        
        # Remove ourselves from the poll object
        if self._fileno is not None:
            try:
                asyncore.poller.unregister(self._fileno)
            except KeyError:
                pass

    def close(self):
        self.del_channel()
        if self.socket is not None:
            self.socket.close()
    
    # -----------------------------------------------------------------------
    # We only want to be writable if we're connecting, or something is in our
    # buffer.
    def writable(self):
        return (not self.connected) or len(self._writebuf)
    
    # Send some data from our buffer when we can write
    def handle_write(self):
        #self.logger.debug('%d wants to write!', self._fileno)
        
        if not self.writable():
            # We don't have any buffer, silly thing
            asyncore.poller.register(self._fileno, select.POLLIN)
            return
        
        sent = asyncore.dispatcher.send(self, self._writebuf[self._pointer:])
        self._pointer += sent
        
        # We've run out of data
        if self._pointer == len(self._writebuf):
            self._writebuf = ''
            self._pointer = 0
            asyncore.poller.register(self._fileno, select.POLLIN)
        
        # If we're posting, we might need to read some more data from our file
        if self.mode == MODE_POST_DATA:
            self.parent._bytes += sent
            if len(self._writebuf) == 0:
                self.post_data()
    
    # -----------------------------------------------------------------------
    # We want buffered output, duh
    def send(self, data):
        self._writebuf += data
        # We need to know about writable things now
        asyncore.poller.register(self._fileno)
        #self.logger.debug('%d has data!', self._fileno)
    
    # -----------------------------------------------------------------------
    
    def handle_error(self):
        self.logger.exception('%d: unhandled exception!', self.connid)
    
    # -----------------------------------------------------------------------
    
    def handle_connect(self):
        self.status = STATE_CONNECTED
        self.logger.debug('%d: connected!', self.connid)
    
    def handle_close(self):
        self.really_close()
    
    def really_close(self, error=None):
        self.mode = MODE_COMMAND
        self.status = STATE_DISCONNECTED
        
        self.close()
        self.reset()
        
        if error and hasattr(error, 'args'):
            self.logger.warning('%d: %s!', self.connid, error.args[1])
            self.reconnect_at = time.time() + self.parent.conf['server']['reconnect_delay']
        else:
            self.logger.warning('%d: Connection closed: %s', self.connid, error)
    
    # There is some data waiting to be read
    def handle_read(self):
        try:
            self._readbuf += self.recv(16384)
        except socket.error, msg:
            self.really_close(msg)
            return
        
        # Split the buffer into lines. Last line is always incomplete.
        lines = self._readbuf.split('\r\n')
        self._readbuf = lines.pop()
        
        # Do something useful here
        for line in lines:
            self.logger.debug('%d: < %s', self.connid, line)

            # Initial login stuff
            if self.mode == MODE_AUTH:
                resp = line.split(None, 1)[0]
                
                # Welcome... post, no post
                if resp in ('200', '201'):
                    if self.username:
                        text = 'AUTHINFO USER %s\r\n' % (self.username)
                        self.send(text)
                        self.logger.debug('%d: > AUTHINFO USER ********', self.connid)
                    else:
                        self.mode = MODE_COMMAND
                        self.parent._idle.append(self)
                        self.logger.debug('%d: ready.', self.connid)
                
                # Need password too
                elif resp in ('381'):
                    if self.password:
                        text = 'AUTHINFO PASS %s\r\n' % (self.password)
                        self.send(text)
                        self.logger.debug('%d: > AUTHINFO PASS ********', self.connid)
                    else:
                        self.really_close('need password!')
                
                # Auth ok
                elif resp in ('281'):
                    self.mode = MODE_COMMAND
                    self.parent._idle.append(self)
                    self.logger.debug('%d: ready.', self.connid)
                
                # Auth failure
                elif resp in ('502'):
                    self.really_close('authentication failure.')
                
                # Dunno
                else:
                    self.logger.warning('%d: unknown response while MODE_AUTH - "%s"',
                        self.connid, line)
            
            # Posting a file
            elif self.mode == MODE_POST_INIT:
                resp = line.split(None, 1)[0]
                # Posting is allowed
                if resp == '340':
                    self.mode = MODE_POST_DATA
                    
                    # TODO: use the suggested message-ID, will require some rethinking as to how
                    #       messages are constructed
                    m = MSGID_RE.search(line)
                    if m:
                        self.logger.debug('%d: changing Message-ID to %s', self.connid, m.group(1))
                        self._article.headers['Message-ID'] = m.group(1)

                    # Prepare the article for posting
                    article_size = self._article.prepare()
                    self.parent.remember_msgid(article_size, self._article)

                    self.post_data()
                
                # Posting is not allowed
                elif resp == '440':
                    self.mode = MODE_COMMAND
                    self.parent._idle.append(self)
                    del self._article
                    self.logger.warning('%d: posting not allowed!', self.connid)
                
                # WTF?
                else:
                    self.logger.warning('%d: unknown response while MODE_POST_INIT - "%s"',
                        self.connid, line)
            
            # Done posting
            elif self.mode == MODE_POST_DONE:
                resp = line.split(None, 1)[0]
                # Ok
                if resp == '240':
                    #self.parent.post_success(self._article)

                    self.mode = MODE_COMMAND
                    self.parent._idle.append(self)

                # Not ok
                elif resp.startswith('44'):
                    self.mode = MODE_COMMAND
                    self.parent._idle.append(self)
                    self.logger.warning('%d: posting failed - %s', self.connid, line)
                
                # WTF?
                else:
                    self.logger.warning('%d: unknown response while MODE_POST_DONE - "%s"',
                        self.connid, line)
            
            # Other stuff
            else:
                self.logger.warning('%d: unknown response from server - "%s"',
                    self.connid, line)
    
    # -----------------------------------------------------------------------
    # Guess what this does!
    def post_article(self, article):
        self.mode = MODE_POST_INIT
        self._article = article
        self.send('POST\r\n')
        self.logger.debug('%d: > POST', self.connid)
    
    def post_data(self):
        data = self._article.postfile.read(POST_READ_SIZE)
        if len(data) == 0:
            self.mode = MODE_POST_DONE
            self._article.postfile.close()
            self._article.postfile = None
        
        self.send(data)

# ---------------------------------------------------------------------------
