#!/usr/bin/arch -i386 /usr/bin/python2.6
"""
Setup/build script for LBN EBB Optionifier (py2app on a Mac)

Copyright (c) 2013, Jake Hartz. All rights reserved.
Use of this source code is governed by a BSD-style license
that can be found in the LICENSE.txt file.

Usage (Mac OS X):
    ./setup-mac.py

    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "dist/LBN EBB Optionifier.app"
"""

import os, sys, shutil, time, subprocess
from setuptools import setup

from vars import metadata, PLUGINS_LOCAL_BASE_DIR, PLUGINS_REMOTE_BASE_DIR

def get_folder(path):
    if isinstance(path, list):
        return [get_folder(i) for i in path]
    else:
        return (path, [os.path.join(path, i) for i in os.listdir(path) if i[:1] != "." and os.path.isfile(os.path.join(path, i))])

if sys.platform != "darwin":
    print "ERROR: This build script is for Macs only."
elif sys.version_info < (2, 6):
    print "ERROR: Requires Python 2.6 or greater."
else:
    if "py2app" not in sys.argv:
        sys.argv.insert(1, "py2app")
    
    data_files = [get_folder("resources")]
    
    rm_local_base_dir = False
    if os.path.isdir(PLUGINS_LOCAL_BASE_DIR) == False:
        for loc in PLUGINS_REMOTE_BASE_DIR:
            if os.path.exists(os.path.join(loc, "plugins.js")):
                os.mkdir(PLUGINS_LOCAL_BASE_DIR)
                rm_local_base_dir = True
                shutil.copy(os.path.join(loc, "plugins.js"), os.path.join(PLUGINS_LOCAL_BASE_DIR, "plugins.js"))
                if os.path.isdir(os.path.join(loc, "plugins")):
                    shutil.copytree(os.path.join(loc, "plugins"), os.path.join(PLUGINS_LOCAL_BASE_DIR, "plugins"))
                break
    if os.path.isdir(PLUGINS_LOCAL_BASE_DIR):
        data_files.append(get_folder(PLUGINS_LOCAL_BASE_DIR))
        if os.path.isdir(os.path.join(PLUGINS_LOCAL_BASE_DIR, "plugins")):
            data_files.append(get_folder(os.path.join(PLUGINS_LOCAL_BASE_DIR, "plugins")))
    
    options = {
        "setup_requires": ["py2app"],
        "app": ["optionifier.py"],
        "data_files": data_files,
        "options": {
            "py2app": {
                "argv_emulation": True,
                "iconfile": "resources/icon.icns",
                "plist": {
                    "CFBundleIdentifier": "com.github.jhartz.lbn-ebb-optionifier",
                    "CFBundleGetInfoString": metadata.description,
                    "NSHumanReadableCopyright": metadata.copyright,
                    "LSArchitecturePriority": [
                        "i386"
                    ],
                    "UTExportedTypeDeclarations": [
                        {
                            "UTTypeIdentifier": "com.github.jhartz.lbn-ebb-optionifier.leo",
                            "UTTypeDescription": "LBN EBB Options",
                            "UTTypeConformsTo": [
                                "public.data"
                            ],
                            "UTTypeTagSpecification": {
                                "public.filename-extension": ["leo"]
                            }
                        }
                    ],
                    "CFBundleDocumentTypes": [
                        {
                            "CFBundleTypeIconFile": "icon.icns",
                            "CFBundleTypeName": "LBN EBB Options",
                            "LSItemContentTypes": [
                                "com.github.jhartz.lbn-ebb-optionifier.leo"
                            ],
                            "CFBundleTypeRole": "Editor",
                            "LSHandlerRank": "Owner"
                        }
                    ]
                }
            }
        }
    }
    
    setup_options = dict(metadata.items() + options.items())
    setup(**setup_options)
    
    if rm_local_base_dir:
        shutil.rmtree(PLUGINS_LOCAL_BASE_DIR)