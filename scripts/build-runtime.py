#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the per-application Qt glass runtime against the installed Qt/KF ABI."""
from pathlib import Path
import shutil
import subprocess
ROOT = Path(__file__).resolve().parents[1]
build = ROOT / 'build/runtime'
subprocess.run(['cmake', '-S', str(ROOT / 'runtime'), '-B', str(build), '-DCMAKE_BUILD_TYPE=Release'], check=True)
subprocess.run(['cmake', '--build', str(build), '-j', '4'], check=True)
bundle = ROOT / 'build/runtime-bundle'
(bundle / 'plugins/generic').mkdir(parents=True, exist_ok=True)
shutil.copy2(build / 'plugins/generic/libpanelglass.so', bundle / 'plugins/generic/libpanelglass.so')
shutil.copy2(ROOT / 'runtime/PanelGlassTransparent.colors', bundle / 'PanelGlassTransparent.colors')
print('Runtime ready: ' + str(bundle))
