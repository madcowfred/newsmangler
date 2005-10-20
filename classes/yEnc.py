# ---------------------------------------------------------------------------
# $Id$
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

"""Useful functions for yEnc encoding/decoding."""

import re

try:
	import _yenc
except ImportError:
	HAVE_YENC = False
else:
	HAVE_YENC = True

# ---------------------------------------------------------------------------
# Translation tables
YDEC_TRANS = ''.join([chr((i + 256 - 42) % 256) for i in range(256)])
YENC_TRANS = ''.join([chr((i + 42) % 256) for i in range(256)])

def yDecode(data):
	# unescape NUL, TAB, LF, CR, ., =
	for i in (0, 9, 10, 13, 46, 61):
		j = '=%c' % (i + 64)
		data = data.replace(j, chr(i))
	
	return data.translate(YDEC_TRANS)

def yEncode(postfile, data, linelen=128):
	'Encode data into yEnc format'
	
	translated = data.translate(YENC_TRANS)
	
	# escape =, NUL, LF, CR
	for i in (61, 0, 10, 13):
		j = '=%c' % (i + 64)
		translated = translated.replace(chr(i), j)
	
	# split the rest of it into lines
	lines = []
	start = 0
	end = 0
	datalen = len(translated)
	
	while end < datalen:
		end = min(datalen, start + linelen)
		# escaped char on the end of the line
		if translated[end-1:end] == '=':
			end += 1
		
		line = translated[start:end]
		
		# dot at the start of the line
		if line[0] == '.':
			line = '.%s' % (line)
		# escape tab/space at the start of a line
		if line[0] in ('\x09', '\x20'):
			line = '=%c%s' % (ord(line[0]) + 64, line[1:])
		# escape tab/space at the end of a line
		if line[-1] in ('\x09', '\x20'):
			line = '%s=%c' % (line[:-1], ord(line[-1]) + 64)
		
		postfile.write(line)
		postfile.write('\r\n')
		start = end

# ---------------------------------------------------------------------------

YSPLIT_RE = re.compile(r'(\S+)=')
def ySplit(line):
	'Split a =y* line into key/value pairs'
	fields = {}
	
	parts = YSPLIT_RE.split(line)[1:]
	if len(parts) % 2:
		return fields
	
	for i in range(0, len(parts), 2):
		key, value = parts[i], parts[i+1]
		fields[key] = value.strip()
	
	return fields

# ---------------------------------------------------------------------------
# Possibly use psyco to speed up encoding slightly (25-30% on 500KB parts)
try:
	import psyco
except ImportError:
	pass
else:
	psyco.bind(yEncode)
