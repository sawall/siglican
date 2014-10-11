siglican
========

A static gallery generator plugin for Pelican, based on the Sigal
Colorbox/Galleria static site generator.

##How To
1. Add this package to your Pelican plugins directory.
2. Add 'siglican' to PLUGINS in pelicanconf.py. Add SIGLICAN_ settings to
   pelicanconf.py as desired (see "Pelican Configuration Settings" below for
   a complete list).
3. Create a *siglican* directory in your base directory, at the same level as
   *content*.
4. Drag gallery.md from examples to your pelican *pages* directory and edit it.
   This gives Pelican a hook into your root gallery.
5. Drag siglican_gallery.html into your Pelican theme's *templates* directory.
   This is the template for your root gallery.
6. Copy one of the example themes to *siglican*. This dictates how album pages
   look. Modify to your heart's content.
7. Make sure your Pelican theme's base.html template has a 'head' block
   (e.g., **{% block head %}{% endblock %}**) defined before **&lt;/head&gt;**.
   That will give your siglican theme a way to inject gallery-specific css and
   javascript into your gallery pages. 
8. Create an 'images' folder under 'siglican'. Add album folders along with
   images and metadata. See *examples/images* for simple examples or the 
   [Sigal documentation](http://sigal.readthedocs.org/en/latest/) for more
   details.

###Example directory excerpt:
```
   /site
      /content/
         /pages/gallery.md
      /plugins/siglican/*.py
      /siglican
         /images
            /album1
            /album2
            /...
         /[colorbox|galleria]
            /static/*
            /templates/album.html
      /themes/theme/templates/siglican_gallery.html
```

###Pelican Configuration Settings

These are the default values of the settings that can be configured in 
pelicanconf.py:

* SIGLICAN_ALBUMS_SORT_REVERSE: False
* SIGLICAN_AUTOROTATE_IMAGES: True
* SIGLICAN_COLORBOX_COLUMN_SIZE: 4
* SIGLICAN_COPY_EXIF_DATA: False
* SIGLICAN_DESTINATION: 'gallery'
* SIGLICAN_FILES_TO_COPY: ()
* SIGLICAN_IGNORE_DIRECTORIES: ['.']
* SIGLICAN_IGNORE_FILES: []
* SIGLICAN_IMG_PROCESSOR: 'ResizeToFit'
* SIGLICAN_IMG_SIZE: (640, 480)
* SIGLICAN_INDEX_IN_URL: False
* SIGLICAN_JPG_OPTIONS: {'quality': 85, 'optimize': True, 'progressive': True}
* SIGLICAN_LINKS: ''
* SIGLICAN_LOCALE: ''
* SIGLICAN_MEDIAS_SORT_ATTR: 'filename'
* SIGLICAN_MEDIAS_SORT_REVERSE: False
* SIGLICAN_MAKE_THUMBS: True
* SIGLICAN_ORIG_DIR: 'original'
* SIGLICAN_ORIG_LINK: False
* SIGLICAN_SOURCE: 'siglican'
* SIGLICAN_THEME: 'colorbox'
* SIGLICAN_THUMB_DIR: 'thumbs'
* SIGLICAN_THUMB_FIT: True
* SIGLICAN_THUMB_PREFIX: ''
* SIGLICAN_THUMB_SIZE: (200, 150)
* SIGLICAN_THUMB_SUFFIX: ''
* SIGLICAN_VIDEO_SIZE: (480, 360)
* SIGLICAN_WEBM_OPTIONS: ['-crf', '10', '-b:v', '1.6M','-qmin', '4', '-qmax', '63']
* SIGLICAN_WRITE_HTML: True
* SIGLICAN_ZIP_GALLERY: False
* SIGLICAN_ZIP_MEDIA_FORMAT: 'resized'

## Future
1. Unit tests.
2. Update colorbox/galleria example themes to deal better with nested albums.
3. Streamline/refactor/merge modules.

## Notes
For more on creating Pelican generator plugins, see the [Pelican plugin documentation]
(http://docs.getpelican.com/en/latest/plugins.html#how-to-create-plugins) and
[Pelican internals](http://docs.getpelican.com/en/latest/internals.html).

##Credits
* Around 2/3 of the core Python code is ported from
  [Sigal v0.8.0](http://sigal.saimon.org/) by Simon Conseil.
* Heavily leverages Pelican, PIL, Jinja2, Colorbox, and Galleria.
* Pelican generator plugin implementation and integration by Scott Boone (sawall@github).