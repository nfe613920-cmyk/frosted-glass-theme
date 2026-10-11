#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import runpy
from pathlib import Path
import sys

stylesheet = Path.home() / '.local/share/konsole/PanelGlass.qss'
env = os.environ.copy()
helper = Path.home() / '.local/opt/panelglass-runtime/popup-launcher.py'
if helper.is_file():
    env = runpy.run_path(str(helper))['environment']('/usr/bin/konsole', env)
os.execve('/usr/bin/konsole', ['/usr/bin/konsole', '-stylesheet', str(stylesheet)] + sys.argv[1:], env)
