===========
newsmangler
===========

newsmangler is a basic client for posting to Usenet. The only notable feature is
multiple connection support to efficiently utilize modern bandwidth.

Installation
============
Copy sample.conf to ~/.newsmangler.conf, edit the options as appropriate.

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

Run ``python poster.py --help`` for other options.
