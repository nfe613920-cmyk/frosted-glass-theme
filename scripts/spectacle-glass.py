#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
from pathlib import Path
import sys
binary = Path.home() / '.local/opt/spectacle-glass/bin/spectacle'
env = os.environ.copy()
env['SPECTACLE_PANEL_GLASS'] = '1'
os.execve(str(binary), [str(binary)] + sys.argv[1:], env)
