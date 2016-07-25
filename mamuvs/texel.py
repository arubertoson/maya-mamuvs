"""
"""
import math
import logging

import maya.api.OpenMaya as api

import mampy
from mampy.dgcontainers import SelectionList
from mampy.dgcomps import MeshPolygon
from mampy.utils import undoable, repeatable

from mamuvs.utils import get_shells


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


__all__ = ['get_average_texel_density', 'get_texel_density', 'set_texel_density']


class TexelDensity(object):
    """Qt class"""


class UV3DArea(object):

    def __init__(self, comp):

        if not comp:
            faces = MeshPolygon(comp.dagpath).get_complete()
        else:
            faces = comp.to_face()

        self.comp = faces
        self.uv = 0.0
        self.surface = 0.0

        self.mesh = comp.mesh
        self.points = self.mesh.getPoints(space=api.MSpace.kWorld)
        self.internal_distance = api.MDistance.internalToUI
        self.get_polygon_uv = self.mesh.getPolygonUV
        self.get_polygon_vert = self.mesh.getPolygonVertices

        self.update()

    @property
    def ratio(self):
        return math.sqrt(self.surface / self.uv)

    def _get_uv_area(self, idx):
        """
        Return uv area of given face index.
        """
        verts = self.get_polygon_vert(idx)
        vert_len = len(verts) - 1

        au, av = self.get_polygon_uv(idx, 0)
        for i in xrange(1, vert_len):
            if i + 1 > vert_len:
                break
            bu, bv = self.get_polygon_uv(idx, i)
            cu, cv = self.get_polygon_uv(idx, i + 1)
            s = (bu - au) * (cv - av)
            t = (cu - au) * (bv - av)
            self.uv += abs((s - t) * 0.5)

    def _get_surface_area(self, idx):
        """
        Return surface area of given face index.
        """
        verts = self.get_polygon_vert(idx)
        vert_len = len(verts) - 1

        a = self.points[verts[0]]
        for i in xrange(1, vert_len):
            if i + 1 > vert_len:
                break
            b = self.points[verts[i]]
            c = self.points[verts[i + 1]]

            la = a.distanceTo(b)
            lb = a.distanceTo(c)
            lc = b.distanceTo(c)

            # convert to internal distance
            la = self.internal_distance(la)
            lb = self.internal_distance(lb)
            lc = self.internal_distance(lc)

            s = (la + lb + lc) * 0.5
            self.surface += math.sqrt(s * (s - la) * (s - lb) * (s - lc))

    def update(self):
        self.uv = 0.0
        self.surface = 0.0
        for idx in self.comp.indices:
            self._get_uv_area(idx)
            self._get_surface_area(idx)


def get_areas():
    s = mampy.selected()
    if not s:
        logger.warn('Nothing selected.')

    return [UV3DArea(c) for c in s.itercomps()]


def get_average_density(areas, texture_size):
    return (sum([a.ratio for a in areas]) / len(areas)) * texture_size


def get_density(areas=None, texture_size=1024):
    return sum([a.ratio for a in areas or get_areas()]) * texture_size


@undoable
@repeatable
def set_density(shell=True, target_density=0, texture_size=1024):
    if shell:
        areas = [UV3DArea(c) for c in get_shells()]
    else:
        selected = mampy.selected()
        components = SelectionList()
        components.extend([c.get_complete() for c in selected.itercomps()])
        areas = [UV3DArea(c) for c in get_shells(components)]

    if target_density == 0:
        target_density = get_average_density(areas, texture_size)

    print areas
    for area in areas:
        scale_value = (area.ratio * texture_size) / target_density
        print scale_value

        uvs = area.comp.to_map()
        print uvs
        point = uvs.bounding_box.center
        uvs.translate(su=scale_value, sv=scale_value, pu=point.u, pv=point.v)

