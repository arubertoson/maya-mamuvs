"""
Mamuvs Maya scripts.

Mamuvs is a high performance collection of functions when working with uvs in Autodesk
Maya.

:copyright: (c) 2016 by Marcus Albertsson
:license: MIT, see LICENSE for details
"""
__author__ = "Marcus Albertsson <marcus.arubertoson@gmail.com>"
__copyright__ = 'Copyright 2016 Marcus Albertsson'
__url__ = "http://github.com/arubertoson/mamuvs"
__version__ = "0.1.0"
__license__ = "MIT"


import os
import json

from mamuvs.align import *
from mamuvs.texel_density import *
from mamuvs.utils import *


class Config(dict):
    """
    Config dict object.

    Written to make mamprefs isolated from the userPref file.
    """
    def __init__(self, file_=None):
        _config_file = file_ or os.path.join(cwd, config_file_name)
        with open(_config_file, 'rb') as f:
            data = json.loads(f.read())

        self._config_file = _config_file
        super(Config, self).__init__(data)

    def __setitem__(self, key, value):
        super(Config, self).__setitem__(key, value)
        self.dump()

    def dump(self):
        with open(self._config_file, 'wb') as f:
            json.dump(self, f, indent=4, sort_keys=True)


config = Config()
config_file_name = '.mamuvs'
cwd = os.path.abspath(os.path.dirname(__file__))