"""
"""
import logging

from maya import cmds

import mampy
from mampy.datatypes import Line2D
from mampy.dgcontainers import SelectionList
from mampy.dgcomps import MeshMap
from mampy.utils import grouped, undoable, repeatable


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


def get_shells(components=None):
    """
    Collect selected uv shells.
    """
    s = components or mampy.selected()
    if not s:
        h = mampy.ls(hl=True)
        if not h:
            return logger.warn('Nothing selected.')
        s.extend(h)

    shells = SelectionList()
    for c in s.itercomps():
        if not c:
            print 'test'
            c = MeshMap(c.dagpath).get_complete()
        else:
            c = c.to_map()

        count, array = c.mesh.getUvShellsIds()
        wanted = set([array[idx] for idx in c.indices])

        for each in wanted:
            shell = MeshMap.create(c.dagpath)
            shell.add([idx for idx, num in enumerate(array) if num == each])
            shells.append(shell)
    return list(shells.itercomps())


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


if __name__ == '__main__':
    pass
