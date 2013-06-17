# -*- coding: cp936 -*-
from distutils.core import setup
import py2exe

options = {"py2exe":
    {"compressed": 0, 
     "optimize": 2,
     "bundle_files": 1,
      "dll_excludes": ["cudart.dll"]
    }
    }

setup(console=['music2picture.py'],options = options)
