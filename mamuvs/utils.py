"""
"""
import logging

from maya import cmds

import mampy
from mampy.datatypes import Line2D
from mampy.dgcontainers import SelectionList
from mampy.dgcomps import MeshMap
from mampy.utils import grouped, undoable, repeatable
from mampy.computils import get_shells


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


__all__ = ['tear_off', 'orient', 'translate', 'rotate', 'mirror']


@undoable
@repeatable
def tear_off():
    """
    Creates a new uv shell from selected faces.
    """
    s = mampy.selected()

    for comp in s.itercomps():
        if not comp.is_face():
            continue

        edges = comp.to_edge(border=True)
        cmds.polyMapCut(list(edges))
    cmds.select(list(s))


@undoable
@repeatable
def orient():
    """
    Orients shell to closest 90 degree angle on selection.
    """
    s = mampy.ordered_selection(fl=True)
    if not s:
        return logger.warn('Nothing selected.')

    if s[0].is_map():
        new, current = SelectionList(), list(s)
        print current
        for pair in grouped(current, 2):
            new.append(MeshMap(pair))
        s = new

    for comp in s.itercomps():

        if not comp.is_map():
            comp = comp.to_map()
        if len(comp) > 2:
            logger.warn('Does not support border edges or multiple selections.')
            continue

        line = Line2D(*comp.points)
        shell = comp.get_uv_shell()
        shell.translate(a=line.angle, pu=line.center.u, pv=line.center.v)


@undoable
@repeatable
def translate(u=0.0, v=0.0):
    for shell in get_shells():
        shell.translate(u=u, v=v)


@undoable
@repeatable
def rotate(angle):
    for shell in get_shells():
        point = shell.bounding_box.center
        shell.translate(angle=angle, pu=point.u, pv=point.v)


@undoable
@repeatable
def mirror(mode):
    try:
        mirror = {
            'u': 'su',
            'v': 'sv',
        }[mode]
    except KeyError:
        return logger.warn('{} is not a valid mode for mirror'.format(mode))

    for shell in get_shells():
        point = shell.bounding_box.center
        shell.translate(**{mirror: -1, 'pu': point.u, 'pv': point.v})


def shell_border_edges_to_hard():
    """
    Sets uv border edges on a mesh has hard, and everythign else as soft.
    """
    objList = cmds.ls(sl=True, o=True)
    finalBorder = []

    for subObj in objList:
        cmds.select(subObj, r=True)
        cmds.polyNormalPerVertex(ufn=True)
        cmds.polySoftEdge(subObj, a=180, ch=1)
        cmds.select(subObj + '.map[*]', r=True)

        polySelectBorderShell(borderOnly=True)

        uvBorder = cmds.polyListComponentConversion(te=True, internal=True)
        uvBorder = cmds.ls(uvBorder, fl=True)

        for curEdge in uvBorder:
            edgeUVs = cmds.polyListComponentConversion(curEdge, tuv=True)
            edgeUVs = cmds.ls(edgeUVs, fl=True)

            if len(edgeUVs) > 2:
                finalBorder.append(curEdge)

        cmds.polySoftEdge(finalBorder, a=0, ch=1)

    cmds.select(objList)


if __name__ == '__main__':
    pass
