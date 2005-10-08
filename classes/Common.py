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

"""Various miscellaneous useful functions."""

__version__ = '0.01'

import logging
import os
import zlib

# ---------------------------------------------------------------------------
# Parse our configuration file
def ParseConfig():
	configfile = os.path.expanduser('~/.newsmangler.conf')
	if not os.path.isfile(configfile):
		print 'ERROR: config file "%s" is missing!' % (configfile)
		sys.exit(1)
	
	c = ConfigParser()
	c.read(configfile)
	conf = {}
	for section in c.sections():
		conf[section] = {}
		for option in c.options(section):
			v = c.get(section, option)
			if v.isdigit():
				v = int(v)
			conf[section][option] = v
	
	return conf

# Create our logger
def CreateLogger():
	logger = logging.getLogger('mangler')
	handler = logging.StreamHandler()
	formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.INFO)
	return logger

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

# Escape things properly to work as XML entities
def XMLBrackets(s):
	s = s.replace('<', '&lt;')
	s = s.replace('>', '&gt;')
	s = s.replace('"', '&#34;')
	return s

# ---------------------------------------------------------------------------
