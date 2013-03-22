"""
LBN EBB Optionifier common variables

Copyright (c) 2013, Jake Hartz. All rights reserved.
Use of this source code is governed by a BSD-style license
that can be found in the LICENSE.txt file.
"""

import os

class Struct(dict):
    """A dict that can be accessed like an object."""
    # Some ideas from http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
    
    def __init__(self, obj={}):
        for key, value in obj.iteritems():
            if isinstance(value, dict):
                # Convert from dict to Struct
                obj[key] = Struct(value)
        dict.__init__(self, obj)
    
    def __setitem__(self, key, value):
        if isinstance(value, dict):
            return dict.__setitem__(self, key, Struct(value))
        else:
            return dict.__setitem__(self, key, value)
    
    def __getattr__(self, key):
        return self.__getitem__(key)
    
    def __setattr__(self, key, value):
        return self.__setitem__(key, value)
    
    def __delattr__(self, key):
        return self.__delitem__(key)
    
    def __repr__(self):
        # Slightly prettier than default (object keys aren't put through repr)
        return "{" + ", ".join("%s: %s" % (key, repr(value)) for (key, value) in self.iteritems()) + "}"


metadata = Struct({
    "name": "LBN EBB Optionifier",
    "author": "Jake Hartz",
    "author_email": "jhartz@github.com",
    "version": "1.0",
    "copyright": "Copyright (C) 2013 Jake Hartz",
    "description": "Options file generator for the LBN Electronic Bulletin Board",
    "license": "BSD-style two-clause license (LICENSE.txt)",
    "url": "http://jhartz.github.com/"
})

PLUGINS_LOCAL_BASE_DIR = "data"  # location of plugins.js and the plugins directory
PLUGINS_REMOTE_BASE_DIR = [os.path.join("..", "EBB")]  # possible locations for plugins.js and the plugins directory (not inside codebase)
