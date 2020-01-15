import os
import imantics as im


from PIL import Image
from mongoengine import *

import io
import cv2
import numpy as np
from urllib.parse import urlparse

import tensorflow as tf
gfile = tf.io.gfile

from .events import Event, SessionEvent
from .datasets import DatasetModel
from .annotations import AnnotationModel

import logging
logger = logging.getLogger('gunicorn.error')

def isfile(path):
    return os.path.isfile(path) if os.path.exists(path) \
        else gfile.exists(path) and not gfile.isdir(path)

class ImageModel(DynamicDocument):

    COCO_PROPERTIES = ["id", "width", "height", "file_name", "path", "license",\
                       "flickr_url", "coco_url", "date_captured", "dataset_id"]

    # -- Contants
    THUMBNAIL_DIRECTORY = '.thumbnail'
    PATTERN = (".gif", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".GIF", ".PNG", ".JPG", ".JPEG", ".BMP", ".TIF", ".TIFF")

    # Set maximum thumbnail size (h x w) to use on dataset page
    MAX_THUMBNAIL_DIM = (1024, 1024)

    # -- Private
    _dataset = None

    # -- Database
    id = SequenceField(primary_key=True)
    dataset_id = IntField(required=True)
    category_ids = ListField(default=[])

    # Absolute path to image file
    path = StringField(required=True, unique=True)
    width = IntField(required=True)
    height = IntField(required=True)
    file_name = StringField()

    # True if the image is annotated
    annotated = BooleanField(default=False)
    # Poeple currently annotation the image
    annotating = ListField(default=[])
    num_annotations = IntField(default=0)

    thumbnail_url = StringField()
    image_url = StringField()
    coco_url = StringField()
    date_captured = DateTimeField()

    metadata = DictField()
    license = IntField()

    deleted = BooleanField(default=False)
    deleted_date = DateTimeField()

    milliseconds = IntField(default=0)
    events = EmbeddedDocumentListField(Event)
    regenerate_thumbnail = BooleanField(default=False)

    @classmethod
    def create_from_path(cls, path, dataset_id=None):

        fp = gfile.GFile(path, 'rb')
        pil_image = Image.open(fp)

        image = cls()
        image.file_name = os.path.basename(path)
        image.path = path
        image.width = pil_image.size[0]
        image.height = pil_image.size[1]

        if dataset_id is not None:
            image.dataset_id = dataset_id
        else:
            # Get dataset name from path
            folders = path.split('/')
            i = folders.index("datasets")
            dataset_name = folders[i+1]

            dataset = DatasetModel.objects(name=dataset_name).first()
            if dataset is not None:
                image.dataset_id = dataset.id

        pil_image.close()

        return image

    def delete(self, *args, **kwargs):
        self.thumbnail_delete()
        AnnotationModel.objects(image_id=self.id).delete()
        return super(ImageModel, self).delete(*args, **kwargs)

    def thumbnail(self, size, path_only=False):
        """
        Generates (if required) and returns thumbnail
        """
        if size is None:
            size = self.MAX_THUMBNAIL_DIM

        thumbnail_path = self.thumbnail_path(size)

        if self.regenerate_thumbnail or \
            not isfile(thumbnail_path):

            logger.debug(f'Generating thumbnail for {self.id}')

            pil_image = self.generate_thumbnail()
            pil_image = pil_image.convert("RGB")

            # Resize image to fit in MAX_THUMBNAIL_DIM envelope as necessary
            pil_image.thumbnail((self.MAX_THUMBNAIL_DIM[1], self.MAX_THUMBNAIL_DIM[0]))

            buf = io.BytesIO()

            # Save as a jpeg to improve loading time
            # (note file extension will not match but allows for backwards compatibility)
            with gfile.GFile(thumbnail_path, 'wb') as fp:
                pil_image.save(buf, "JPEG", quality=80, optimize=True, progressive=True)
                fp.write(buf.getvalue())

            self.update(is_modified=False)

            if not path_only:
                buf.seek(0)
                return buf
        else:
            if not path_only:
                return gfile.GFile(thumbnail_path, 'rb')

        return thumbnail_path

    def thumbnail_path(self, size):
        parsed = urlparse(self.path)
        width, height = size

        folders = parsed.path.split('/')
        folders.insert(len(folders)-1, self.THUMBNAIL_DIRECTORY)

        filename = os.path.basename(parsed.path)
        root, ext = os.path.splitext(filename)
        folders[len(folders)-1] = root + f'.{width}x{height}' + ext

        path = parsed._replace(path='/'.join(folders)).geturl()
        directory = os.path.dirname(path)

        if not gfile.exists(directory):
            gfile.makedirs(directory)

        return path

    def thumbnail_delete(self):
        path = self.thumbnail_path()
        if isfile(path):
            gfile.remove(path)

    def generate_thumbnail(self):
        image = self().draw(color_by_category=True, bbox=False)
        return Image.fromarray(image)

    def flag_thumbnail(self, flag=True):
        """
        Toggles values to regenerate thumbnail on next thumbnail request
        """
        if self.regenerate_thumbnail != flag:
            self.update(regenerate_thumbnail=flag)

    def copy_annotations(self, annotations):
        """
        Creates a copy of the annotations for this image
        :param annotations: QuerySet of annotation models
        :return: number of annotations
        """
        annotations = annotations.filter(
            width=self.width, height=self.height, area__gt=0).exclude('events')

        for annotation in annotations:
            clone = annotation.clone()

            clone.dataset_id = self.dataset_id
            clone.image_id = self.id

            clone.save(copy=True)

        return annotations.count()

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = DatasetModel.objects(id=self.dataset_id).first()
        return self._dataset

    def __call__(self):

        fp = gfile.GFile(self.path, 'rb')
        image_array = np.fromstring(fp.read(), dtype=np.uint8)

        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = im.Image(image, path=self.path)

        for annotation in AnnotationModel.objects(image_id=self.id, deleted=False).all():
            if not annotation.is_empty():
                image.add(annotation())

        return image

    def can_delete(self, user):
        return user.can_delete(self.dataset)

    def can_download(self, user):
        return user.can_download(self.dataset)

    # TODO: Fix why using the functions throws an error
    def permissions(self, user):
        return {
            'delete': True,
            'download': True
        }

    def add_event(self, e):
        u = {
            'push__events': e,
        }
        if isinstance(e, SessionEvent):
            u['inc__milliseconds'] = e.milliseconds

        self.update(**u)


__all__ = ["ImageModel"]
