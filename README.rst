===========
newsmangler
===========

newsmangler is a basic client for posting to Usenet. The only notable feature is
multiple connection support to efficiently utilize modern bandwidth.

Installation
============
#. Download the source: ``git clone git://github.com/madcowfred/newsmangler.git``

#. Copy sample.conf to ~/.newsmangler.conf, edit the options as appropriate.

#. Download and install the `yenc module <https://bitbucket.org/dual75/yenc>`_
   for greatly improved yEnc encoding speed.

Usage
=====
Make a directory containing the files you wish to post, the _directory name_ will
be used as the post subject. For example:

test post please ignore/
 - test.part1.rar
 - test.part2.rar

Will post as:
  ``test post please ignore [1/2] - "test.part1.rar" yEnc (01/27)``
  ``test post please ignore [2/2] - "test.part2.rar" yEnc (01/27)``

Run ``python mangler.py --help`` for other options.
