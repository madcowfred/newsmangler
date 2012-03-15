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

"""Useful functions for yEnc encoding/decoding."""

import re
import zlib

# ---------------------------------------------------------------------------

HAVE_PSYCO = False
HAVE_YENC = False
HAVE_YENC_FRED = False

# ---------------------------------------------------------------------------
# Translation tables
YDEC_TRANS = ''.join([chr((i + 256 - 42) % 256) for i in range(256)])
YENC_TRANS = ''.join([chr((i + 42) % 256) for i in range(256)])

YDEC_MAP = {}
for i in range(256):
	YDEC_MAP[chr(i)] = chr((i + 256 - 64) % 256)

# ---------------------------------------------------------------------------

def yDecode(data):
	# unescape any escaped char (grr)
	data = re.sub(r'=(.)', yunescape, data)
	return data.translate(YDEC_TRANS)

def yunescape(m):
	return YDEC_MAP[m.group(1)]

def yEncode_C(postfile, data):
	# If we don't have my modified yenc module, we have to do the . quoting
	# ourselves. This is about 50% slower.
	if HAVE_YENC_FRED:
		yenced, tempcrc = _yenc.encode_string(data, escapedots=1)[:2]
	else:
		yenced, tempcrc = _yenc.encode_string(data)[:2]
		yenced = yenced.replace('\r\n.', '\r\n..')
	
	postfile.write(yenced)
	
	if not yenced.endswith('\r\n'):
		postfile.write('\r\n')
	
	return '%08x' % ((tempcrc ^ -1) & 2**32L - 1)

def yEncode_Python(postfile, data, linelen=128):
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
		line = translated[start:end]
		
		# FIXME: line consisting entirely of a space/tab
		if start == end - 1:
			if line[0] in ('\x09', '\x20'):
				line = '=%c' % (ord(line[0]) + 64)
		else:
			# escape tab/space/period at the start of a line
			if line[0] in ('\x09', '\x20'):
				line = '=%c%s' % (ord(line[0]) + 64, line[1:-1])
				end -= 1
			elif line[0] == '\x2e':
				line = '.%s' % (line)
			
			# escaped char on the end of the line
			if line[-1] == '=':
				line += translated[end]
				end += 1
			# escape tab/space at the end of a line
			elif line[-1] in ('\x09', '\x20'):
				line = '%s=%c' % (line[:-1], ord(line[-1]) + 64)
		
		postfile.write(line)
		postfile.write('\r\n')
		start = end
	
	return CRC32(data)

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

def yEncMode():
	if HAVE_YENC_FRED:
		return 'yenc-fred'
	elif HAVE_YENC:
		return 'yenc-vanilla'
	elif HAVE_PSYCO:
		return 'python-psyco'
	else:
		return 'python-vanilla'

# ---------------------------------------------------------------------------
# Make a human readable CRC32 value
def CRC32(data):
	return '%08x' % (zlib.crc32(data) & 2**32L - 1)

# Come up with a 'safe' filename
def SafeFilename(filename):
	safe_filename = os.path.basename(filename)
	for char in [' ', "\\", '|', '/', ':', '*', '?', '<', '>']:
		safe_filename = safe_filename.replace(char, '_')
	return safe_filename

# ---------------------------------------------------------------------------
# Use the _yenc C module if it's available. If not, try to use psyco to speed
# up part encoding 25-30%.
try:
	import _yenc
except ImportError:
	try:
		import psyco
	except ImportError:
		pass
	else:
		HAVE_PSYCO = True
		psyco.bind(yEncode_Python)
	yEncode = yEncode_Python
else:
	HAVE_YENC = True
	HAVE_YENC_FRED = ('Freddie mod' in _yenc.__doc__)
	yEncode = yEncode_C
