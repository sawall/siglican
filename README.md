siglican
========

A static gallery generator plugin for Pelican, based on the Sigal
Colorbox/Galleria generator by Simon Conseil.

##Notes

* The bulk of the code is ported from [Sigal v0.8.0](http://sigal.saimon.org/).
* Removal of Sigal process handling, rewriting Sigal settings variables, and
  integration as a Pelican Generator plugin by Scott Boone.
* The core python code used to generate gallery directories and images as well
  as to populate the Jinja environment with album metadata is in beta. Jinja 
  templates are incomplete.

## To Do
1. Update galleria theme to work.
2. Change settings names to something other than SIGAL_*
3. Unit tests.
4. Logging cleanup.
5. General code and documentation cleanup.