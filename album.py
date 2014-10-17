# -*- coding:utf-8 -*-

# Album classes for use with siglican plugin along with some helper
# methods for context building. This code is largely a copy of gallery.py
# from Sigal.

# Copyright (c) 2009-2014 - Simon Conseil
# Copyright (c) 2013      - Christophe-Marie Duquesne

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

# siglican:
# Copyright (c) 2014      - Scott Boone (https://github.com/sawall/)
# Minor updates from Sigal.

import os
import logging

from collections import defaultdict
from PIL import Image as PILImage

from .compat import strxfrm, UnicodeMixin, url_quote
from .utils import read_markdown, url_from_path
from .image import process_image, get_exif_tags

class Media(UnicodeMixin):
    """Base Class for media files.

    Attributes:

    - ``type``: ``"image"`` or ``"video"``.
    - ``filename``: Filename of the resized image.
    - ``thumbnail``: Location of the corresponding thumbnail image.
    - ``big``: If not None, location of the unmodified image.
    - ``exif``: If not None contains a dict with the most common tags. For more
        information, see :ref:`simple-exif-data`.
    - ``raw_exif``: If not ``None``, it contains the raw EXIF tags.

    """

    type = ''
    extensions = ()

    def __init__(self, filename, path, settings):
        self.src_filename = self.filename = self.url = filename
        self.path = path
        self.settings = settings
        
        self.src_path = os.path.join(settings['SIGLICAN_SOURCE'], path, filename)
        self.dst_path = os.path.join(settings['SIGLICAN_DESTINATION'], path, filename)
        
        self.thumb_name = get_thumb(self.settings, self.filename)
        self.thumb_path = os.path.join(settings['SIGLICAN_DESTINATION'], path, self.thumb_name)
        
        self.logger = logging.getLogger(__name__)
        self.raw_exif = None
        self.exif = None
        self.date = None
        self._get_metadata()
        #signals.media_initialized.send(self)

    def __repr__(self):
        return "<%s>(%r)" % (self.__class__.__name__, str(self))

    def __unicode__(self):
        return os.path.join(self.path, self.filename)

    @property
    def thumbnail(self):
        """Path to the thumbnail image (relative to the album directory)."""
        # cleanup: make this deal better with SIGLICAN_MAKE_THUMBS: False
        return url_from_path(self.thumb_name)

    def _get_metadata(self):
        """ Get image metadata from filename.md: title, description, meta."""
        self.description = ''
        self.meta = {}
        self.title = ''
        
        descfile = os.path.splitext(self.src_path)[0] + '.md'
        if os.path.isfile(descfile):
            meta = read_markdown(descfile)
            for key, val in meta.items():
                setattr(self, key, val)


class Image(Media):
    """Gather all informations on an image file."""
    
    type = 'image'
    extensions = ('.jpg', '.jpeg', '.png')
    
    def __init__(self, filename, path, settings):
        super(Image, self).__init__(filename, path, settings)
        self.raw_exif, self.exif = get_exif_tags(self.src_path)
        if self.exif is not None and 'dateobj' in self.exif:
            self.date = self.exif['dateobj']


class Video(Media):
    """Gather all informations on a video file."""

    type = 'video'
    extensions = ('.mov', '.avi', '.mp4', '.webm', '.ogv')

    def __init__(self, filename, path, settings):
        super(Video, self).__init__(filename, path, settings)
        base = os.path.splitext(filename)[0]
        self.src_filename = filename
        self.filename = self.url = base + '.webm'
        self.dst_path = os.path.join(settings['SIGLICAN_DESTINATION'], path, base + '.webm')


# minimally modified from Sigal's gallery.Album class
class Album(object):
    description_file = "index.md"
    output_file = 'index.html'

    def __init__(self, path, settings, dirnames, filenames, gallery):
        self.path = path
        self.name = path.split(os.path.sep)[-1]
        self.gallery = gallery
        self.settings = settings
        self.orig_path = None
        self._thumbnail = None

        # set up source and destination paths
        if path == '.':
            self.src_path = settings['SIGLICAN_SOURCE']
            self.dst_path = settings['SIGLICAN_DESTINATION']
        else:
            self.src_path = os.path.join(settings['SIGLICAN_SOURCE'], path)
            self.dst_path = os.path.join(settings['SIGLICAN_DESTINATION'], path)

        self.logger = logging.getLogger(__name__)
        self._get_metadata()  # this reads the index.md file

        # optionally add index.html to the URLs
        # ** don't understand purpose of this; default is False
        self.url_ext = self.output_file if settings['SIGLICAN_INDEX_IN_URL'] else ''
        
        # creates appropriate subdirectory for the album
        self.index_url = url_from_path(os.path.relpath(
            settings['SIGLICAN_DESTINATION'], self.dst_path)) + '/' + self.url_ext

        # sort sub-albums
        dirnames.sort(key=strxfrm, reverse=settings['SIGLICAN_ALBUMS_SORT_REVERSE'])
        self.subdirs = dirnames

        #: List of all medias in the album (:class:`~sigal.gallery.Image` and
        #: :class:`~sigal.gallery.Video`).
        self.medias = medias = []
        self.medias_count = defaultdict(int)
        
        # create Media objects
        for f in filenames:
            ext = os.path.splitext(f)[1]
            if ext.lower() in Image.extensions:
                media = Image(f, self.path, settings)
            elif ext.lower() in Video.extensions:
                media = Video(f, self.path, settings)
            else:
                continue

            self.medias_count[media.type] += 1
            medias.append(media)

        # sort images
        if medias:
            medias_sort_attr = settings['SIGLICAN_MEDIAS_SORT_ATTR']
            if medias_sort_attr == 'date':
                key = lambda s: s.date or datetime.now()
            else:
                key = lambda s: strxfrm(getattr(s, medias_sort_attr))

            medias.sort(key=key, reverse=settings['SIGLICAN_MEDIAS_SORT_REVERSE'])

        #signals.album_initialized.send(self)
    
    # string representation of Album for debug statements
    def __repr__(self):
        return "<%s>(path=%r, title=%r, assets:%r)" % (self.__class__.__name__,
                self.path, self.title, self.medias)

    def __unicode__(self):
        return (u"{} : ".format(self.path) +
                ', '.join("{} {}s".format(count, _type)
                          for _type, count in self.medias_count.items()))

    def __len__(self):
        return len(self.medias)

    def __iter__(self):
        return iter(self.medias)

    def _get_metadata(self):
        """Get album metadata from `description_file` (`index.md`):

        -> title, thumbnail image, description

        """
        descfile = os.path.join(self.src_path, self.description_file)
        self.description = ''
        self.meta = {}
        # default: get title from directory name
        self.title = os.path.basename(self.path if self.path != '.'
                                      else self.src_path)

        if os.path.isfile(descfile):
            meta = read_markdown(descfile)
            for key, val in meta.items():
                setattr(self, key, val)

    def create_output_directories(self):
        """Create output directories for thumbnails and original images."""
        
        def check_or_create_dir(path):
            if not os.path.isdir(path):
                os.makedirs(path)

        check_or_create_dir(self.dst_path)

        if self.medias:
            check_or_create_dir(os.path.join(self.dst_path,
                                     self.settings['SIGLICAN_THUMB_DIR']))

        #if self.medias and self.settings['SIGLICAN_KEEP_ORIG']:
        #    self.orig_path = os.path.join(self.dst_path, self.settings['SIGLICAN_ORIG_DIR'])
        #    check_or_create_dir(self.orig_path)

    @property
    def images(self):
        """List of images (:class:`~sigal.gallery.Image`)."""
        for media in self.medias:
            if media.type == 'image':
                yield media

    @property
    def videos(self):
        """List of videos (:class:`~sigal.gallery.Video`)."""
        for media in self.medias:
            if media.type == 'video':
                yield media

    @property
    def albums(self):
        """List of :class:`~sigal.gallery.Album` objects for each
        sub-directory.
        """
        root_path = self.path if self.path != '.' else ''
        return [self.gallery.albums[os.path.join(root_path, path)]
                for path in self.subdirs]

    @property
    def url(self):
        """URL of the album, relative to its parent."""
        url = self.name.encode('utf-8')
        return url_quote(url) + '/' + self.url_ext

    @property
    def thumbnail(self):
        """Path to the thumbnail of the album."""

        if self._thumbnail:
            # stop if it is already set
            return url_from_path(self._thumbnail)

        # Test the thumbnail from the Markdown file.
        thumbnail = self.meta.get('thumbnail', [''])[0]

        if thumbnail and os.path.isfile(os.path.join(self.src_path, thumbnail)):
            self._thumbnail = os.path.join(self.name, get_thumb(self.settings,
                                                        thumbnail))
            self.logger.debug("Thumbnail for %r : %s", self, self._thumbnail)
            return url_from_path(self._thumbnail)
        else:
            # find and return the first landscape image
            for f in self.medias:
                ext = os.path.splitext(f.filename)[1]
                if ext.lower() in Image.extensions:
                    im = PILImage.open(f.src_path)
                    if im.size[0] > im.size[1]:
                        self._thumbnail = os.path.join(self.name, f.thumbnail)
                        self.logger.debug(
                            "Use 1st landscape image as thumbnail for %r : %s",
                            self, self._thumbnail)
                        return url_from_path(self._thumbnail)

            # else simply return the 1st media file
            if not self._thumbnail and self.medias:
                self._thumbnail = os.path.join(self.name, self.medias[0].thumbnail)
                self.logger.debug("Use the 1st image as thumbnail for %r : %s",
                                  self, self._thumbnail)
                return url_from_path(self._thumbnail)

            # use the thumbnail of their sub-directories
            if not self._thumbnail:
                for path, album in self.gallery.get_albums(self.path):
                    if album.thumbnail:
                        self._thumbnail = os.path.join(self.name, album.thumbnail)
                        self.logger.debug(
                            "Using thumbnail from sub-directory for %r : %s",
                            self, self._thumbnail)
                        return url_from_path(self._thumbnail)

        self.logger.error('Thumbnail not found for %r', self)
        return None

    @property
    def breadcrumb(self):
        """List of ``(url, title)`` tuples defining the current breadcrumb
        path.
        """
        if self.path == '.':
            return []

        path = self.path
        breadcrumb = [((self.url_ext or '.'), self.title)]

        while True:
            path = os.path.normpath(os.path.join(path, '..'))
            if path == '.':
                break

            url = (url_from_path(os.path.relpath(path, self.path)) + '/' +
                   self.url_ext)
            breadcrumb.append((url, self.gallery.albums[path].title))

        breadcrumb.reverse()
        return breadcrumb
    
    # TODO: delete this and related settings; this is not a use case that
    # a Pelican plugin should handle
    @property
    def zip(self):
        """Make a ZIP archive with all media files and return its path.

        If the ``zip_gallery`` setting is set,it contains the location of a zip
        archive with all original images of the corresponding directory.

        """
        zip_gallery = self.settings['SIGLICAN_ZIP_GALLERY']

        if zip_gallery and len(self) > 0:
            archive_path = os.path.join(self.dst_path, zip_gallery)
            archive = zipfile.ZipFile(archive_path, 'w')

            if self.settings['SIGLICAN_ZIP_MEDIA_FORMAT'] == 'orig':
                for p in self:
                    archive.write(p.src_path, os.path.split(p.src_path)[1])
            else:
                for p in self:
                    archive.write(p.dst_path, os.path.split(p.dst_path)[1])

            archive.close()
            self.logger.debug('Created ZIP archive %s', archive_path)
            return zip_gallery
        else:
            return None

# ** TODO: move as part of utils cleanup
def get_thumb(settings, filename):
    """Return the path to the thumb.

    examples:
    >>> default_settings = create_settings()
    >>> get_thumb(default_settings, "bar/foo.jpg")
    "bar/thumbnails/foo.jpg"
    >>> get_thumb(default_settings, "bar/foo.png")
    "bar/thumbnails/foo.png"

    for videos, it returns a jpg file:
    >>> get_thumb(default_settings, "bar/foo.webm")
    "bar/thumbnails/foo.jpg"
    """

    path, filen = os.path.split(filename)
    name, ext = os.path.splitext(filen)

    if ext.lower() in Video.extensions:
        ext = '.jpg'
    return os.path.join(path, settings['SIGLICAN_THUMB_DIR'], settings['SIGLICAN_THUMB_PREFIX'] +
                name + settings['SIGLICAN_THUMB_SUFFIX'] + ext)
