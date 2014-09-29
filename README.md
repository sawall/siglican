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
1. Determine the best approach for merging Pelican and Sigal web themes. This
   will probably require putting Sigal theme information into the Pelican theme
   in order to facilitate loading Javascript and CSS in the html headers.
2. Revise Sigal colorbox and galleria themes for easy inclusion into Pelican
   themes.
3. Change settings names to something other than SIGAL_*
4. Unit tests.
5. Logging cleanup.
6. General code and documentation cleanup.