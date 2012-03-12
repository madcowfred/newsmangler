# ---------------------------------------------------------------------------
# $Id: poster.py 3875 2005-10-03 08:19:19Z freddie $
# ---------------------------------------------------------------------------
# Copyright (c) 2005, freddie@madcowdisease.org
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

"""Base class for leecher/mangler."""

import asyncore
import logging
import os
import select
import sys
import time

from newsmangler.asyncnntp import asyncNNTP

# ---------------------------------------------------------------------------

class BaseMangler:
	def __init__(self, conf, debug):
		self.conf = conf
	
		self._conns = []
		self._idle = []
		
		# Create our logger
		self.logger = logging.getLogger('mangler')
		handler = logging.StreamHandler()
		formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
		handler.setFormatter(formatter)
		self.logger.addHandler(handler)
		if debug:
			self.logger.setLevel(logging.DEBUG)
		else:
			self.logger.setLevel(logging.INFO)
		
		# Create a poll object for async bits to use. If the user doesn't have
		# poll, we're going to have to fake it.
		try:
			asyncore.poller = select.poll()
		except AttributeError:
			from classes.FakePoll import FakePoll
			asyncore.poller = FakePoll()
	
	# Connect to server
	def connect(self):
		for i in range(self.conf['server']['connections']):
			conn = asyncNNTP(self, i, self.conf['server']['hostname'],
				self.conf['server']['port'], None, self.conf['server']['username'],
				self.conf['server']['password'],
			)
			conn.do_connect()
			self._conns.append(conn)

	# Poll our poll() object and do whatever is neccessary. Basically a combination
	# of asyncore.poll2() and asyncore.readwrite(), without all the frippery.
	def poll(self):
		results = asyncore.poller.poll(0)
		for fd, flags in results:
			obj = asyncore.socket_map.get(fd)
			if obj is None:
				self.logger.warning('Invalid FD for poll() - %d', fd)
			
			try:
				if flags & (select.POLLIN | select.POLLPRI):
					obj.handle_read_event()
				if flags & select.POLLOUT:
					obj.handle_write_event()
				if flags & (select.POLLERR | select.POLLHUP | select.POLLNVAL):
					obj.handle_expt_event()
			except asyncore.ExitNow:
				raise
			except:
				obj.handle_error()

# ---------------------------------------------------------------------------
