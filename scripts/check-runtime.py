#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check input, dock construction, repeated paints and async Qt Quick card feedback."""
import os
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
build = ROOT / 'build/runtime-tests'
subprocess.run(['cmake', '-S', str(ROOT / 'runtime'), '-B', str(build), '-DCMAKE_BUILD_TYPE=Release', '-DPANELGLASS_TESTS=ON'], check=True)
subprocess.run(['cmake', '--build', str(build), '-j', '4'], check=True)
env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
       'PANEL_GLASS_SCHEME': str(ROOT / 'runtime/PanelGlassTransparent.colors'),
       'QT_PLUGIN_PATH': str(build / 'plugins'), 'QT_QPA_GENERIC_PLUGINS': 'panelglass'}
subprocess.run([str(build / 'panelglass-test')], env=env, check=True)

env['PANEL_GLASS_POPUPS_ONLY'] = '1'
subprocess.run([str(build / 'panelglass-test')], env=env, check=True)
