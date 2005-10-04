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

"""Controls stuff."""

import asyncore
import os
import select
from cStringIO import StringIO

from classes import yEnc

# ---------------------------------------------------------------------------

class Controller:
	def __init__(self, conf):
		self.conf = conf
		
		self._articles = []
		self._files = {}
		
		# Set up our poller
		asyncore.poller = select.poll()
	
	def post(self, dirs):
		self.generate_part_list(dirs)
	
	# -----------------------------------------------------------------------
	# Generate the list of articles we need to post
	def generate_article_list(self, dirs):
		for dirname in dirs:
			if dirname.endswith(os.sep):
				dirname = dirname[:-len(os.sep)]
			if not dirname:
				continue
			
			article_size = self.conf['posting']['article_size']
			
			# Get a list of useful files
			f = os.listdir(dirname)
			files = []
			for filename in f:
				filepath = os.path.join(dirname, filename)
				# Skip non-files and empty files
				if os.path.isfile(filepath) and os.path.getsize(filepath):
					files.append(filename)
			files.sort()
			
			n = 1
			for filename in files:
				filepath = os.path.join(dirname, filename)
				filesize = os.path.getsize(filepath)
				
				full, partial = divmod(filesize, article_size)
				if partial:
					parts = full + 1
				else:
					parts = full
				
				# Build a subject
				temp = '%%0%sd' % (len(str(len(files))))
				filenum = temp % (n)
				subject = '%s [%s/%d] - "%s" yEnc (%%s/%d)' % (dirname, filenum, len(files), filename, parts)
				
				# Now make up our parts
				for i in range(parts):
					article = [filepath, subject, i+1]
					self._articles.append(part)
				
				n += 1
	
	# -----------------------------------------------------------------------
	# Build an article for posting.
	def build_article(self):
		(f, filepathfilesize) = self._files[0]
		#if f is None:
		#	self._files[0][0] = f = open(
		
		#self._part += 1
		data = f.read(self.conf['posting']['article_size'])
		
		# If we've just hit the end of the file, we can throw it away now
		if (self._part * self.conf['posting']['article_size'] > filesize):
			f.close()
			self._files.pop(0)

# ---------------------------------------------------------------------------
