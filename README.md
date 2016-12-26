ansible-modules-jfenal
======================

This repo contains a few modules I'm working on.

Reporting bugs
==============

Please send me a mail at jfenal at redhat dot com or jfenal at gmail dot com

Testing modules
===============

Each module has a test suite in the test directory. You may have to supply the right inventory file to run them.

License
=======

There modules are licensed under the GPLv3, as Anisble Core is.

Installation
============

Fork it and add the resulting directory to your Ansible library path.

  mkdir $HOME/dev
  cd $HOME/dev
  git clone https://github.com/jfenal/ansible-modules-jfenal.git
  ANSIBLE_LIBRARY="$HOME/dev/ansible-modules-jfenal" 
  export ANSIBLE_LIBRARY


