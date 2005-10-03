#!/usr/bin/env python
# ---------------------------------------------------------------------------
# $Id $
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

"""Posts stuff."""

import os
import sys
from ConfigParser import ConfigParser
from optparse import OptionParser

from classes.Controller import Controller

# ---------------------------------------------------------------------------

def main():
	# Parse our command line options
	parser = OptionParser(usage='usage: %prog [options] dir1 dir2 ... dirN')
	parser.add_option('-g', '--group',
		dest='group',
		help='post to a different group than the default',
	)
	parser.add_option('-n', '--nzbs',
		action='store_true',
		dest='generate_nzbs',
		default=False,
		help='generate a .NZB file for each post',
	)
	
	(options, args) = parser.parse_args()
	
	# No args? We have nothing to do!
	if not args:
		parser.print_help()
		sys.exit(1)
	
	# Make sure at least one of the args exists
	dirs = []
	for arg in args:
		if os.path.isdir(arg):
			dirs.append(arg)
		else:
			print 'ERROR: "%s" does not exist!' % (arg)
	
	if not dirs:
		print 'ERROR: no valid directories provided on command line!'
		sys.exit(1)
	
	# And off we go
	c = Controller(options, dirs)
	c.run_forever()

# ---------------------------------------------------------------------------

if __name__ == '__main__':
	main()
