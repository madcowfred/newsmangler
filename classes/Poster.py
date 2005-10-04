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

"""Main class for posting stuff."""

import asyncore
import os
import select
import time
from cStringIO import StringIO
from zlib import crc32

from classes import yEnc

__version__ = 'moo'

# ---------------------------------------------------------------------------

class Poster:
	def __init__(self, conf, newsgroup):
		self.conf = conf
		self.newsgroup = newsgroup
		
		self._articles = []
		self._files = {}
		
		# Set up our poller
		asyncore.poller = select.poll()
	
	def post(self, dirs):
		self.generate_article_list(dirs)
		
		for article in self._articles[:1]:
			postfile = StringIO()
			self.build_article(postfile, article)
	
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
				fileinfo = {
					'filename': filename,
					'filepath': filepath,
					'filesize': filesize,
					'parts': parts,
				}
				
				for i in range(parts):
					article = [fileinfo, subject, i+1]
					self._articles.append(article)
				
				n += 1
	
	# -----------------------------------------------------------------------
	# Build an article for posting.
	def build_article(self, postfile, article):
		(fileinfo, subject, partnum) = article
		
		# Read the chunk of data from the file
		f = self._files.get(fileinfo['filepath'], None)
		if f is None:
			self._files[fileinfo['filepath']] = f = open(fileinfo['filepath'], 'rb')
		
		begin = f.tell()
		data = f.read(self.conf['posting']['article_size'])
		end = f.tell()
		
		# If that was the last part, close the file and throw it away
		if partnum == fileinfo['parts']:
			self._files[fileinfo['filepath']].close()
			del self._files[fileinfo['filepath']]
		
		# Basic headers
		line = 'From: %s\n' % (self.conf['posting']['from'])
		postfile.write(line)
		line = 'Newsgroups: %s\n' % (self.newsgroup)
		postfile.write(line)
		line = time.strftime('Date: %a, %d %b %Y %H:%M:%S UTC\n', time.gmtime())
		postfile.write(line)
		subj = subject % (partnum)
		line = 'Subject: %s\n' % (subj)
		postfile.write(line)
		line = 'X-Newsposter: newsmangler %s - http://www.madcowdisease.org/mcd/newsmangler\n' % (__version__)
		postfile.write(line)
		#mid = '<%s@%s>' % (time.time(), )
		#postfile.write('Message-ID: %s\n' % mid)
		postfile.write('\n')
		
		# yEnc start
		line = '=ybegin part=%d total=%d line=256 size=%d name=%s\n' % (
			partnum, fileinfo['parts'], fileinfo['filesize'], fileinfo['filename']
		)
		postfile.write(line)
		line = '=ypart begin=%d end=%d\n' % (begin, end)
		postfile.write(line)
		
		# yEnc data
		yEnc.yEncode(postfile, data)
		
		# yEnc end
		partcrc = '%08x' % (crc32(data) & 2**32L - 1)
		line = '=yend size=%d part=%d pcrc32=%s\n' % (end-begin, partnum, partcrc)
		postfile.write(line)
		
		# And done
		postfile.write('.\n')
		
		postfile.seek(0, 0)
		print postfile.read()

# ---------------------------------------------------------------------------
