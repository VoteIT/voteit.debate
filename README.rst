Plenary debate for VoteIT
=========================

.. image:: https://travis-ci.org/VoteIT/voteit.debate.png?branch=master
   :target: https://travis-ci.org/VoteIT/voteit.debate

This package is for physical meetings with plenary debates. It's part of the VoteIT project.

Main functions
--------------

* Multiple speaker queues per Agenda item
* Projector views for speakers within active queue
* Keeps track of time for each speaker
* Multiple lists and ability to promote speakers who haven't spoken before
* "Safe positions" for speakers who're about to speak. (They won't get moved down if someone else wants to speak)
* Speakers are able to add or remove themselves form the speaker list

Installation
------------

This package requires voteit.core and voteit.irl.
Simply add the package names to your paster ini file in the plugins section.

plugins = 
    voteit.debate

For more help, see the VoteIT documentation.
