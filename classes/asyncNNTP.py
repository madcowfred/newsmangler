"A basic NNTP client based on asyncore_buffered from blamehangle."

import asyncore
import errno
import logging
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
		self._postfile = None
		
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
		self.logger.debug('%d: SO_SNDBUF is %s', self.connid,
			self.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
		
		# If we have to bind our socket to an IP, do that
		#if self.bindto is not None:
		#	self.bind((self.bindto, 0))
		
		# Try to connect. This can blow up!
		try:
			self.connect((self.host, self.port))
		except (socket.error, socket.gaierror), msg:
			self.really_close(msg)
		else:
			self.state = STATE_CONNECTING
			self.logger.info('%d: connecting to %s:%s', self.connid, self.host, self.port)
	
	def add_channel(self):
		asyncore.socket_map[self._fileno] = self
		# Add ourselves to the poll object
		asyncore.poller.register(self._fileno)
	
	def del_channel(self):
		# Remove ourselves from the async map
		if asyncore.socket_map.has_key(self._fileno):
			del asyncore.socket_map[self._fileno]
		
		# Remove ourselves from the poll object
		try:
			asyncore.poller.unregister(self._fileno)
		except KeyError:
			pass
	
	def close(self):
		self.del_channel()
		if self.socket is not None:
			self.socket.close()
	
	# We only want to be writable if we're connecting, or something is in our
	# buffer.
	def writable(self):
		return (not self.connected) or len(self._writebuf)
	
	# Send some data from our buffer when we can write
	def handle_write(self):
		#self.logger.debug('%d wants to write!', self._fileno)
		
		if not self.writable():
			# We don't have any buffer, silly thing
			#print '%d has no data!' % self._fileno
			asyncore.poller.register(self._fileno, select.POLLIN)
			return
		
		sent = asyncore.dispatcher.send(self, self._writebuf)
		
		self._writebuf = self._writebuf[sent:]
		self.parent._bytes += sent
		
		# If we're posting, we might need to read some more data
		if len(self._writebuf) <= POST_BUFFER_MIN and self.mode == MODE_POST_DATA:
			self.post_data()
	
	# We want buffered output, duh
	def send(self, data):
		self._writebuf += data
		# We need to know about writable things now
		asyncore.poller.register(self._fileno)
		#self.logger.debug('%d has data!', self._fileno)
	
	# -----------------------------------------------------------------------
	
	def handle_error(self):
		self.logger.error('%d: unhandled exception!', self.connid, exc_info=True)
	
	# -----------------------------------------------------------------------
	
	def handle_connect(self):
		self.status = STATE_CONNECTED
		self.logger.info('%d: connected!', self.connid)
	
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
			self.logger.warning('Connection closed: %s', error)
	
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
			# Initial login stuff
			if self.mode == MODE_AUTH:
				resp = line.split(None, 1)[0]
				
				# Welcome... post, no post
				if resp in ('200', '201'):
					if self.username:
						text = 'AUTHINFO USER %s\r\n' % (self.username)
						self.send(text)
					else:
						self.mode = MODE_COMMAND
						self.parent._idle.append(self)
						self.logger.info('%d: ready.', self.connid)
				
				# Need password too
				elif resp in ('381'):
					if self.password:
						text = 'AUTHINFO PASS %s\r\n' % (self.password)
						self.send(text)
					else:
						self.really_close('need password!')
				
				# Auth ok
				elif resp in ('281'):
					self.mode = MODE_COMMAND
					self.parent._idle.append(self)
					self.logger.info('%d: ready.', self.connid)
				
				# Auth failure
				elif resp in ('502'):
					self.really_close('authentication failure.')
				
				# Dunno
				else:
					self.logger.warning('%d: unknown response from server - "%s"',
						self.connid, line)
			
			# Posting a file
			elif self.mode == MODE_POST_INIT:
				resp = line.split(None, 1)[0]
				# Ok
				if resp == '340':
					self.mode = MODE_POST_DATA
					self.logger.debug('%d: posting article.', self.connid)
					
					self.post_data()
				# Not ok
				elif resp == '440':
					self.mode = MODE_COMMAND
					self.parent._idle.append(self)
					del self._postfile
					self.logger.warning('%d: posting not allowed!', self.connid)
			
			# Done posting
			elif self.mode == MODE_POST_DONE:
				resp = line.split(None, 1)[0]
				# Ok
				if resp == '240':
					self.mode = MODE_COMMAND
					self.parent._idle.append(self)
					self.logger.debug('%d: posting complete.', self.connid)
				elif resp.startswith('44'):
					self.mode = MODE_COMMAND
					self.parent._idle.append(self)
					self.logger.warning('%d: posting failed - %s', self.connid, line)
			
			# Other stuff
			else:
				self.logger.warning('%d: unknown response from server - "%s"',
					self.connid, line)
	
	# -----------------------------------------------------------------------
	# Guess what this does!
	def post_article(self, postfile):
		self.mode = MODE_POST_INIT
		self._postfile = postfile
		self.send('POST\n')
	
	def post_data(self):
		data = self._postfile.read(POST_READ_SIZE)
		if len(data) == 0:
			self.mode = MODE_POST_DONE
			self._postfile.close()
			self._postfile = None
		
		self.send(data)

# ---------------------------------------------------------------------------
