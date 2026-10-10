#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
from pathlib import Path
import sys

stylesheet = Path.home() / '.local/share/konsole/PanelGlass.qss'
os.execv('/usr/bin/konsole', ['/usr/bin/konsole', '-stylesheet', str(stylesheet)] + sys.argv[1:])
