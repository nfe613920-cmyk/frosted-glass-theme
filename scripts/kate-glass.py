#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import runpy
from pathlib import Path
import sys
bundle = Path.home() / '.local/opt/kate-glass'
env = os.environ.copy()
env['KATE_PANEL_GLASS'] = '1'
env['LD_LIBRARY_PATH'] = str(bundle / 'lib') + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
helper = Path.home() / '.local/opt/panelglass-runtime/popup-launcher.py'
if helper.is_file():
    env = runpy.run_path(str(helper))['environment'](bundle / 'bin/kate', env)
os.execve(str(bundle / 'bin/kate'), [str(bundle / 'bin/kate'), '--new'] + sys.argv[1:], env)
