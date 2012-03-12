===========
newsmangler
===========

newsmangler is a basic client for posting binaries to Usenet. The only notable
feature is multiple connection support to efficiently utilize modern bandwidth.

Installation
============
#. Download the source: ``git clone git://github.com/madcowfred/newsmangler.git``
   (or download a .zip I guess).

#. Copy sample.conf to ~/.newsmangler.conf, edit the options as appropriate.
   ``cp sample.conf ~/.newsmangler.conf``
   ``nano ~/.newsmangler.conf``

#. Download and install the `yenc module <https://bitbucket.org/dual75/yenc>`_
   for greatly improved yEnc encoding speed.

Usage
=====
Make a directory containing the files you wish to post, the _directory name_ will
be used as the post subject. For example, with a directory structure such as:

test post please ignore/
 - test.nfo
 - test.part1.rar
 - test.part2.rar

And the command line: ``python mangler.py "test post please ignore"``

The files will post as:
  ``test post please ignore [1/3] - "test.nfo" yEnc (1/1)``
  ``test post please ignore [2/3] - "test.part1.rar" yEnc (01/27)``
  ``test post please ignore [3/3] - "test.part2.rar" yEnc (01/27)``

See ``python mangler.py --help`` for other options.
