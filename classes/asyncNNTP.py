"A basic NNTP client based on asyncore_buffered from blamehangle."

import asyncore
import select
import socket
import time

# ---------------------------------------------------------------------------

STATE_DISCONNECTED = 0
STATE_CONNECTING = 1
STATE_CONNECTED = 2

MODE_AUTH = 0
MODE_COMMAND = 1
MODE_DATA = 2

# ---------------------------------------------------------------------------

class asyncNNTP(asyncore.dispatcher):
	def __init__(self, host, port, bindto, username, password):
		asyncore.dispatcher.__init__(self)
		
		self.host = host
		self.port = port
		self.bindto = bindto
		self.username = username
		self.password = password
		
		self.reset()
		
		# Create the socket
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		
		# If we have to bind our socket to an IP, do that
		if self.bindto is not None:
			self.bind((self.bindto, 0))
		
		# Try to connect. This can blow up!
		try:
			self.connect((self.host, self.port))
		except (socket.error, socket.gaierror), msg:
			self.really_close(msg)
		else:
			self.state = STATE_CONNECTING
	
	def reset(self):
		self._readbuf = ''
		self._writebuf = ''
		
		self.connect_retry = 0
		self.mode = MODE_AUTH
		self.state = STATE_DISCONNECTED
	
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
		#print '%d wants to write!' % self._fileno
		
		if not self.writable():
			# We don't have any buffer, silly thing
			#print '%d has no data!' % self._fileno
			asyncore.poller.register(self._fileno, select.POLLIN)
			return
		
		sent = asyncore.dispatcher.send(self, self._writebuf)
		self._writebuf = self._writebuf[sent:]
	
	# We want buffered output, duh
	def send(self, data):
		self._writebuf += data
		# We need to know about writable things now
		asyncore.poller.register(self._fileno)
		#print '%d has data!' % self._fileno
	
	# -----------------------------------------------------------------------
	
	def handle_connect(self):
		self.status = STATE_CONNECTED
	
	def handle_close(self):
		self.really_close()
	
	def really_close(self, error=None):
		self.mode = MODE_COMMAND
		self.status = STATE_DISCONNECTED
		
		self.close()
		self.reset()
		
		print 'BONG! %s' % (error)
	
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
			print '>', line.strip()
			
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
				
				# Need password too
				elif resp in ('381'):
					if self.password:
						text = 'AUTHINFO PASS %s\r\n' % (self.password)
						self.send(text)
					else:
						self.really_close('need password!')
				
				# Auth ok
				if resp in ('281'):
					self.mode = MODE_COMMAND
				
				# Auth failure
				elif resp in ('502'):
					self.really_close('authentication failure.')

# ---------------------------------------------------------------------------

if __name__ == '__main__':
	asyncore.poller = select.poll()
	a = asyncNNTP('news.adelaide.pipenetworks.com', 119, None, None, None)
	while 1:
		results = asyncore.poller.poll()
		for fd, event in results:
			if event & select.POLLIN:
				asyncore.read(a)
			elif event & select.POLLOUT:
				asyncore.write(a)
		
		time.sleep(0.1)
