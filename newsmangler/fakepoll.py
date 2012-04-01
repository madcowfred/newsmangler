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

"Fake poll() for systems that don't implement it (Windows, most notably)."

import select
import socket

# Assume that they need constants
select.POLLIN = 1
select.POLLOUT = 2
select.POLLNVAL = 4
select.POLLPRI = 8
select.POLLERR = 16
select.POLLHUP = 32

# ---------------------------------------------------------------------------

class FakePoll:
	def __init__(self):
		self.FDs = {}
	
	# Register an FD for polling
	def register(self, fd, flags=None):
		if flags is None:
			self.FDs[fd] = select.POLLIN|select.POLLOUT|select.POLLNVAL
		else:
			self.FDs[fd] = flags
	
	# Unregister an FD
	def unregister(self, fd):
		del self.FDs[fd]
	
	# Poll (select!) for timeout seconds. Nasty.
	def poll(self, timeout):
		fds = self.FDs.keys()
		can_read, can_write = select.select(fds, fds, [], timeout)[:2]
		
		results = {}
		
		for fd in can_read:
			results[fd] = select.POLLIN
		for fd in can_write:
			if fd in results:
				results[fd] |= select.POLLOUT
			else:
				results[fd] = select.POLLOUT
		
		return results.items()

# ---------------------------------------------------------------------------
