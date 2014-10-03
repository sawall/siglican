siglican
========

A static gallery generator plugin for Pelican, based on the Sigal
Colorbox/Galleria generator by Simon Conseil.

##How To
1. Create a 'siglican' directory in your base directory (at the same level
   as 'content'.
2. Create an 'images' directory under siglican. Folders under this level are
   albums.
3. Create album and image metadata, as desired.
4. Create theme directory inside of 'siglican'. Use the colorbox or galleria
   theme as a starting point. Make sure that your Pelican theme's base.html
   template has a 'head' block defined before </head>.

## To Do
1. Update galleria theme to work.
2. Change settings names to something other than SIGAL_*
3. Unit tests.
4. Logging cleanup.
5. General code and documentation cleanup.
   
##Credits
* The bulk of the code is ported from [Sigal v0.8.0](http://sigal.saimon.org/).
* Pelican integration by Scott Boone (sawall@github).