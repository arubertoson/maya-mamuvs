"""
"""
import logging
import operator

from mampy.datatypes import BoundingBox
from mampy.utils import undoable, repeatable

import mamuvs
from mamuvs.utils import get_shells


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


class AlignUV(object):

    (MAX_U, MAX_V, MIN_U, MIN_V, CENTER_U, CENTER_V, SCALE_MAX_U, SCALE_MAX_V,
     SCALE_MIN_U, SCALE_MIN_V, DISTRIBUTE_U, DISTRIBUTE_V, SPACE_U,
     SPACE_V) = range(14)

    def __init__(self, mode):
        self.mode = mode
        self.shells = get_shells()

        # properties
        self._bbox = None
        self._span = None
        self._max_width = None
        self._max_height = None
        self._min_width = None
        self._min_height = None
        self._shell_sum = None

        if self.mode in (self.DISTRIBUTE_U, self.SPACE_U):
            self.calc_dir = 'width'
            self.shells.sort(key=operator.attrgetter('bounding_box.center.u'))
        elif self.mode in (self.DISTRIBUTE_V, self.SPACE_V):
            self.calc_dir = 'height'
            self.shells.sort(key=operator.attrgetter('bounding_box.center.v'))

    @property
    def bbox(self):
        if self._bbox is None:
            self._bbox = BoundingBox()
            self._bbox.boxtype = '2D'
            for shell in self.shells:
                self._bbox.expand(shell.bounding_box)
        return self._bbox

    @property
    def max_width(self):
        if self._max_width is None:
            self._max_width = max(shell.bounding_box.width
                                  for shell in self.shells)
        return self._max_width

    @property
    def max_height(self):
        if self._max_height is None:
            self._max_height = max(shell.bounding_box.height
                                   for shell in self.shells)
        return self._max_height

    @property
    def min_width(self):
        if self._min_width is None:
            self._min_width = min(shell.bounding_box.width
                                  for shell in self.shells)
        return self._min_width

    @property
    def min_height(self):
        if self._min_height is None:
            self._min_height = min(shell.bounding_box.height
                                   for shell in self.shells)
        return self._min_height

    @property
    def spanu(self):
        if self._span is None:
            self._span = self.bbox.width / (len(self.shells) - 1)
        return self._span

    @property
    def spanv(self):
        if self._span is None:
            self._span = self.bbox.height / (len(self.shells) - 1)
        return self._span

    @property
    def shell_sum(self):
        if self._shell_sum is None:
            self._shell_sum = sum(getattr(shell.bounding_box, self.calc_dir)
                                  for shell in self.shells)
        return self._shell_sum


@undoable
@repeatable
def align(mode):
    """
    Aligns uvs given mode.
    """
    try:
        align_mode = {
            'maxu': AlignUV.MAX_U,
            'minu': AlignUV.MIN_U,
            'maxv': AlignUV.MAX_V,
            'minv': AlignUV.MIN_V,
            'centeru': AlignUV.CENTER_U,
            'centerv': AlignUV.CENTER_V,
        }[mode]
    except KeyError:
        return logger.warn('{} is not a valid align mode.'.format(mode))

    align = AlignUV(align_mode)
    for shell in align.shells:
        shell.translate(**_get_align_kwargs(shell, align))


@undoable
@repeatable
def scalefit(mode):
    """
    Docstring
    """
    try:
        scale_mode = {
            'maxu': AlignUV.SCALE_MAX_U,
            'minu': AlignUV.SCALE_MIN_U,
            'maxv': AlignUV.SCALE_MAX_V,
            'minv': AlignUV.SCALE_MIN_V,
        }[mode]
    except KeyError:
        return logger.warn('{} is not a valid scalefit mode.'.format(mode))

    align = AlignUV(scale_mode)
    for shell in align.shells:
        u, v = shell.bounding_box.center.u, shell.bounding_box.center.v
        shell.translate(pu=u, pv=v, **_get_align_kwargs(shell, align))


def _get_align_kwargs(shell, align):
    return {
        align.MAX_U: {'u': align.bbox.max.u - shell.bounding_box.max.u},
        align.MIN_U: {'u': align.bbox.min.u - shell.bounding_box.min.u},
        align.MAX_V: {'v': align.bbox.max.v - shell.bounding_box.max.v},
        align.MIN_V: {'v': align.bbox.min.v - shell.bounding_box.min.v},

        align.CENTER_U: {'u': align.bbox.center.u - shell.bounding_box.center.u},
        align.CENTER_V: {'v': align.bbox.center.v - shell.bounding_box.center.v},

        align.SCALE_MAX_U: {'su': align.max_width / shell.bounding_box.width},
        align.SCALE_MIN_U: {'su': align.min_width / shell.bounding_box.width},
        align.SCALE_MAX_V: {'sv': align.max_height / shell.bounding_box.height},
        align.SCALE_MIN_V: {'sv': align.min_height / shell.bounding_box.height},
    }[align.mode]


@undoable
@repeatable
def distribute(mode):
    """
    docstring.
    """
    try:
        dist_mode = {
            'u': AlignUV.DISTRIBUTE_U,
            'v': AlignUV.DISTRIBUTE_V,
        }[mode]
    except KeyError:
        return logger.warn('{} is not a valid distribute mode.'.format(mode))

    align = AlignUV(dist_mode)
    for idx, shell in enumerate(align.shells):
        if idx == 0:
            distance = getattr(align.bbox.min, mode)
            continue
        elif idx == len(align.shells) - 1:
            continue

        distance += align.spanu if mode == 'u' else align.spanv
        translate_value = distance - getattr(shell.bounding_box.center, mode)
        shell.translate(**{mode: translate_value})


@undoable
@repeatable
def space(mode, space=mamuvs.config['CURRENT_ALIGN_SPACE_VALUE']):
    try:
        space_mode = {
            'u': AlignUV.SPACE_U,
            'v': AlignUV.SPACE_V,
        }[mode]
    except KeyError:
        return logger.warn('{} is not valid space mode.'.format(mode))

    align = AlignUV(space_mode)

    spacing = (space * (len(align.shells) - 1) + align.shell_sum) / 2
    calculated_space = getattr(align.bbox.center, mode) - spacing

    for shell in align.shells:
        offset = shell.bounding_box
        shell.translate(**{mode: calculated_space - getattr(offset.min, mode)})

        max_ = getattr(offset.max, mode)
        min_ = getattr(offset.min, mode)
        calculated_space += space + (max_ - min_)
