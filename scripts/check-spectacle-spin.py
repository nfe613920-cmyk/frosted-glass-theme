#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify glass spinbox arrows and text entry against a patched source checkout."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    shutil.copy2(args.source / 'src/Gui/PanelGlassSpinBox.qml', folder / 'PanelGlassSpinBox.qml')
    shutil.copy2(root / 'tests/test-glass-spin.qml', folder / 'tst_glassspin.qml')
    env = os.environ.copy()
    env.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software')
    runner = shutil.which('qmltestrunner') or '/usr/lib/qt6/bin/qmltestrunner'
    subprocess.run([runner, '-input', str(folder)], check=True, env=env)
