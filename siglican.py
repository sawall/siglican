# -*- coding:utf-8 -*-

# Copyright (c) 2014 - Scott Boone
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function

import os
import sys
import locale
import logging
import fnmatch
from pelican import signals
from pelican.generators import Generator
from .compat import PY2
from .album import Album
from .image import process_image
from .video import process_video
from .writer import Writer

logger = logging.getLogger(__name__)

# Default config from Sigal's settings module. These have been changed to 
# upper case because Pelican does not recognize lower case configuration names.
# note: if a default is changed, please also update README.md
_DEFAULT_SIGLICAN_SETTINGS = {
    'SIGLICAN_ALBUMS_SORT_REVERSE': False,
    'SIGLICAN_AUTOROTATE_IMAGES': True,
    'SIGLICAN_COLORBOX_COLUMN_SIZE': 4,
    'SIGLICAN_COPY_EXIF_DATA': False,
    'SIGLICAN_DESTINATION': 'gallery',
    'SIGLICAN_FILES_TO_COPY': (),
    'SIGLICAN_IGNORE_DIRECTORIES': ['.'],
    'SIGLICAN_IGNORE_FILES': [],
    'SIGLICAN_IMG_PROCESSOR': 'ResizeToFit',
    'SIGLICAN_IMG_SIZE': (640, 480),
    'SIGLICAN_INDEX_IN_URL': False,
    'SIGLICAN_JPG_OPTIONS': {'quality': 85, 'optimize': True, 'progressive': True},
    'SIGLICAN_LINKS': '',
    'SIGLICAN_LOCALE': '',
    'SIGLICAN_MEDIAS_SORT_ATTR': 'filename',
    'SIGLICAN_MEDIAS_SORT_REVERSE': False,
#    'SIGLICAN_MAKE_THUMBS': True,
    'SIGLICAN_ORIG_DIR': 'original',
    'SIGLICAN_ORIG_LINK': False,
#    'PLUGINS': [],
#    'PLUGIN_PATHS': [],
    'SIGLICAN_SOURCE': 'siglican',
    'SIGLICAN_THEME': 'colorbox',
    'SIGLICAN_THUMB_DIR': 'thumbs',
    'SIGLICAN_THUMB_FIT': True,
    'SIGLICAN_THUMB_PREFIX': '',
    'SIGLICAN_THUMB_SIZE': (200, 150),
    'SIGLICAN_THUMB_SUFFIX': '',
    'SIGLICAN_VIDEO_SIZE': (480, 360),
    'SIGLICAN_WEBM_OPTIONS': ['-crf', '10', '-b:v', '1.6M',
                              '-qmin', '4', '-qmax', '63'],
    'SIGLICAN_WRITE_HTML': True,
    'SIGLICAN_ZIP_GALLERY': False,
    'SIGLICAN_ZIP_MEDIA_FORMAT': 'resized',
}

# Generator class used to generate plugin context and write.
# TODO github5: consider usinge CachingGenerator instead?
class SigalGalleryGenerator(Generator):
    # reference: methods provided by Pelican Generator:
    # def _update_context(self, items):  adds more items to the context dict
    # def get_template(self, name):  returns templates from theme based on theme
    # def get_files(self, paths, exclude=[], extensions=None):  paths to search, 
    #               exclude, allowed extensions
    
    def __init__(self, *args, **kwargs):
        """Initialize gallery dict and load in custom Sigal settings."""

        logger.debug("siglican: entering SigalGalleryGenerator.__init__")
        self.albums = {}
        # this needs to be first to establish pelican settings:
        super(SigalGalleryGenerator, self).__init__(*args, **kwargs)
        # add default sigal settings to generator settings:
        for k in _DEFAULT_SIGLICAN_SETTINGS.keys()[:]:
            self.settings[k] = self.settings.get(k, _DEFAULT_SIGLICAN_SETTINGS[k])
            #logger.debug("sigal.pelican: setting %s: %s",k,self.settings[k])
        self._clean_settings()
        # this is where we could create a signal if we wanted to, e.g.:
        # signals.gallery_generator_init.send(self)

    def _clean_settings(self):
        """Checks existence of directories and normalizes image size settings."""
        
        # create absolute paths to source, theme and destination directories:
        init_source = self.settings['SIGLICAN_SOURCE']
        self.settings['SIGLICAN_SOURCE'] = os.path.normpath(self.settings['PATH'] + 
            "/../" + self.settings['SIGLICAN_SOURCE'] + '/images')
        self.settings['SIGLICAN_THEME'] = os.path.normpath(self.settings['PATH'] +
            "/../" + init_source + "/" + self.settings['SIGLICAN_THEME'])
        self.settings['SIGLICAN_DESTINATION'] = os.path.normpath(
            self.settings['OUTPUT_PATH'] + "/" + self.settings['SIGLICAN_DESTINATION'])
        
        enc = locale.getpreferredencoding() if PY2 else None
        
        # test for existence of source directories
        pathkeys = ['SIGLICAN_SOURCE', 'SIGLICAN_THEME']
        for k in pathkeys:
            if os.path.isdir(self.settings[k]):
                # convert to unicode for os.walk dirname/filename
                if PY2 and isinstance(self.settings[k], str):
                    self.settings[k] = self.settings[k].decode(enc)
                logger.info("%s = %s",k,self.settings[k])
            else:
                logger.error("siglican: missing source directory %s: %s",
                             k,self.settings[k])
                sys.exit(1)
        
        # normalize sizes as e landscape
        for key in ('SIGLICAN_IMG_SIZE', 'SIGLICAN_THUMB_SIZE', 'SIGLICAN_VIDEO_SIZE'):
            w, h = self.settings[key]
            if h > w:
                self.settings[key] = (h, w)
                logger.warning("siglican: The %s setting should be specified "
                               "with the largest value first.", key)
        
        if not self.settings['SIGLICAN_IMG_PROCESSOR']:
            logger.info('No Processor, images will not be resized')
    
    # based on Sigal's Gallery.__init__() method:    
    def generate_context(self):
        """"Update the global Pelican context that's shared between generators."""

        logger.info("siglican generating context")
        locale.setlocale(locale.LC_ALL, self.settings['SIGLICAN_LOCALE'])
        self.stats = {'image': 0, 'image_skipped': 0,
                      'video': 0, 'video_skipped': 0}
        # build the list of directories with images
        # ** TODO: add error checking, consider use of get(), etc.
        src_path = self.settings['SIGLICAN_SOURCE']
        ignore_dirs = self.settings['SIGLICAN_IGNORE_DIRECTORIES']
        ignore_files = self.settings['SIGLICAN_IGNORE_FILES']
        for path, dirs, files in os.walk(src_path, followlinks=True,
                                         topdown=False):
            relpath = os.path.relpath(path, src_path)
            if ignore_dirs and any(fnmatch.fnmatch(relpath, ignore)
                                   for ignore in ignore_dirs):
                logger.info('siglican: ignoring %s', relpath)
                continue
            if ignore_files: # ** github6: if no ignore_files, then no files?
                files_path = {os.path.join(relpath, f) for f in files}
                for ignore in ignore_files:
                    files_path -= set(fnmatch.filter(files_path, ignore))
                    ## ** TEST? unicode in list may cause mismatch
                logger.debug('siglican: Files before filtering: %r', files)
                files = [os.path.split(f)[1] for f in files_path]
                logger.debug('siglican: Files after filtering: %r', files)
            
            # Remove sub-directories that have been ignored in a previous
            # iteration (as topdown=False, sub-directories are processed before
            # their parent
            for d in dirs[:]:
                path = os.path.join(relpath, d) if relpath != '.' else d
                if path not in self.albums.keys():
                    dirs.remove(d)        
            album = Album(relpath, self.settings, dirs, files, self)

            if not album.medias and not album.albums:
                logger.info('siglican: Skip empty album: %r', album)
            else:
                self.albums[relpath] = album
        # done generating context (self.albums) now
        logger.debug('siglican: albums:\n%r', self.albums.values())

        # update the jinja context so that templates can access it:
        #self._update_context(('albums', ))   # unnecessary? **
        self.context['ALBUMS'] = self.albums  # ** change to SIGLICAN_ALBUMS?

        # update the jinja context with the default sigal settings:
        for k,v in _DEFAULT_SIGLICAN_SETTINGS.iteritems():
            if not k in self.context:
                self.context[k] = v

    def generate_output(self, writer):
        """ Creates gallery destination directories, thumbnails, resized
            images, and moves everything into the destination."""
        
        # note: ignore the writer sent by Pelican because it's not certain
        # which Writer it will send. if another active plugin also implements
        # Writer, Pelican may send that instead of one of its core Writers.
        # I logged a feature request here:
        # https://github.com/getpelican/pelican/issues/1459
        
        # create destination directory
        if not os.path.isdir(self.settings['SIGLICAN_DESTINATION']):
            os.makedirs(self.settings['SIGLICAN_DESTINATION'])
        
        # github7 ** improve exception catching 
        # github8 ** re-integrate multiprocessing logic from Sigal
        
        # generate thumbnails, process images, and move them to the destination
        if logger.getEffectiveLevel() > logging.INFO:
            print('siglican is processing media: ', end='')
            sys.stdout.flush()
        albums = self.albums
        for a in albums:
            logger.info("siglican: processing album: %s",a)
            albums[a].create_output_directories()
            for media in albums[a].medias:
                if logger.getEffectiveLevel() > logging.INFO:
                    print('.', end='')
                    sys.stdout.flush()
                if os.path.isfile(media.dst_path):
                    logger.info("siglican: %s exists - skipping", media.filename)
                    self.stats[media.type + '_skipped'] += 1
                else:
                    logger.info("siglican: processing %r , source: %s, dst: %s",
                             media,media.src_path,media.dst_path)
                    self.stats[media.type] += 1
                    logger.debug("MEDIA TYPE: %s",media.type)
                    # create/move resized images and thumbnails to output dirs:
                    if media.type == 'image':
                        process_image(media.src_path,os.path.dirname(
                                      media.dst_path),self.settings)
                    elif media.type == 'video':
                        process_video(media.src_path,os.path.dirname(
                                      media.dst_path),self.settings)
        if logger.getEffectiveLevel() > logging.INFO:
            print('')
        
        # generate the index.html files for the albums
        if self.settings['SIGLICAN_WRITE_HTML']:  # defaults to True
            # locate the theme; check for a custom theme in ./sigal/themes, if not
            # found, look for a default in siglican/themes
            self.theme = self.settings['SIGLICAN_THEME']
            default_themes = os.path.normpath(os.path.join(
                             os.path.abspath(os.path.dirname(__file__)), 'themes'))
            #logger.debug("siglican: custom theme: %s", self.theme)
            #logger.debug("siglican: default themedir: %s", default_themes)
            if not os.path.exists(self.theme):
                self.theme = os.path.join(default_themes, os.path.basename(self.theme))
                if not os.path.exists(self.theme):
                    raise Exception("siglican: unable to find theme: %s" %
                                     os.path.basename(self.theme))
        
            logger.info("siglican theme: %s", self.theme)
            
            self.writer = Writer(self.context, self.theme, 'album')
            for album in self.albums.values():
                self.writer.write(album)
            
            ## possible cleanup:
            ##   - bring back Writer options that Sigal had?
            ##   - make sure thumbnails don't break in some cases [fixed?]

def get_generators(generators):
    return SigalGalleryGenerator

def register():
    signals.get_generators.connect(get_generators)