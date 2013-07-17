# Copyright (c) 2005-2012, freddie@wafflemonster.org
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

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from cStringIO import StringIO

from newsmangler.yenc import yEncode

class Article:
	def __init__(self, filewrap, begin, end, fileinfo, subject, partnum):
		self._filewrap = filewrap
		self._begin = begin
		self._end = end
		self._fileinfo = fileinfo
		self._subject = subject
		self._partnum = partnum
		
		self.headers = OrderedDict()
		self.postfile = StringIO()

		self.__article_size = 0

	def prepare(self):
		# Don't prepare again if we already did everything
		if self.__article_size > 0:
			self.postfile.seek(0, 0)
			return self.__article_size

		# Headers
		for k, v in self.headers.items():
			self.postfile.write('%s: %s\r\n' % (k, v))
		
		self.postfile.write('\r\n')
		
		# yEnc start
		line = '=ybegin part=%d total=%d line=128 size=%d name=%s\r\n' % (
			self._partnum, self._fileinfo['parts'], self._fileinfo['filesize'], self._fileinfo['filename']
		)
		self.postfile.write(line)
		line = '=ypart begin=%d end=%d\r\n' % (self._begin + 1, self._end)
		self.postfile.write(line)
		
		# yEnc data
		data = self._filewrap.read_part(self._begin, self._end)
		partcrc = yEncode(self.postfile, data)

		# yEnc end
		line = '=yend size=%d part=%d pcrc32=%s\r\n' % (self._end - self._begin, self._partnum, partcrc)
		self.postfile.write(line)
		
		# And done writing for now
		self.postfile.write('.\r\n')
		self.__article_size = self.postfile.tell()
		self.postfile.seek(0, 0)

		return self.__article_size
