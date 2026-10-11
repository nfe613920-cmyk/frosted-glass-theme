#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import runpy
from pathlib import Path
import sys
binary = Path.home() / '.local/opt/spectacle-glass/bin/spectacle'
env = os.environ.copy()
env['SPECTACLE_PANEL_GLASS'] = '1'
helper = Path.home() / '.local/opt/panelglass-runtime/popup-launcher.py'
if helper.is_file():
    env = runpy.run_path(str(helper))['environment'](binary, env)
os.execve(str(binary), [str(binary)] + sys.argv[1:], env)
