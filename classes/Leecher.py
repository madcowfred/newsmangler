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

"""Main class for leeching stuff."""

import asyncore
import os
import select
import sys
import time

from classes import asyncNNTP
from classes import yEnc
from classes.Common import *

# ---------------------------------------------------------------------------

class Leecher(BaseMangler):
	def __init__(self, conf):
		BaseMangler.__init__(self, conf)
	
	def leech(self, nzbs):
		# Connect!
		self.connect()
		
		# And loop
		self._bytes = 0
		last_reconnect = start = time.time()
		
		_sleep = time.sleep
		_time = time.time
		
		while 1:
			now = _time()
			
			# Poll our sockets for events
			self.poll()
			
			# And sleep for a bit to try and cut CPU chompage
			_sleep(0.02)

# ---------------------------------------------------------------------------
