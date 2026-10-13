#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify complete installation and rollback in a temporary home, using built bundles."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)

def main():
    with tempfile.TemporaryDirectory(prefix='panelglass-reuse-') as tmp:
        home = Path(tmp) / 'new user'
        config = home / '.config'; config.mkdir(parents=True)
        old_kwin = '# Keep unrelated settings\n[Plugins]\nblurEnabled=false\n[Desktops]\nNumber=3\n'
        (config / 'kwinrc').write_text(old_kwin)
        panels = config / 'plasma-org.kde.plasma.desktop-appletsrc'
        panels.write_text('Do not touch panel layout\n')
        run(sys.executable, ROOT / 'scripts/restore-all.py', '--apply', '--use-built', '--home', home, '--no-live', stdout=subprocess.DEVNULL)
        for category in ['plasma/desktoptheme', 'plasma/plasmoids', 'konsole', 'color-schemes']:
            base = ROOT / 'assets' / category
            for source in base.rglob('*'):
                if source.is_file():
                    target = home / '.local/share' / category / source.relative_to(base)
                    if source.read_bytes() != target.read_bytes():
                        raise RuntimeError('Installed asset mismatch: ' + str(source.relative_to(ROOT)))
        for app in ['konsole', 'dolphin', 'ark', 'kate', 'kwrite', 'spectacle']:
            launcher = home / '.local/bin' / (app + '-glass')
            if launcher.read_bytes() != (ROOT / 'scripts' / (app + '-glass.py')).read_bytes():
                raise RuntimeError('Launcher mismatch: ' + app)
            # A different HOME exercises path relocation and private library loading.
            env = {**os.environ, 'HOME': str(home), 'QT_QPA_PLATFORM': 'offscreen'}
            result = run(launcher, '--version', env=env, capture_output=True, text=True, timeout=30)
            if not result.stdout.strip():
                raise RuntimeError('Missing application version output: ' + app)
            print('Relocated launcher OK: ' + app)
        expected_editor = ROOT / 'assets/editor-themes/PanelGlass.theme'
        installed_editor = home / '.local/share/org.kde.syntax-highlighting/themes/PanelGlass.theme'
        if expected_editor.read_bytes() != installed_editor.read_bytes():
            raise RuntimeError('Editor theme missing')
        runtime = home / '.local/opt/panelglass-runtime'
        if not (runtime / 'popup-launcher.py').is_file() or not (runtime / 'plugins/generic/libpanelglass.so').is_file():
            raise RuntimeError('Popup runtime incomplete')
        for app in ['konsole', 'dolphin', 'spectacle']:
            desktop = 'org.kde.' + app + '.desktop'
            for directory in ['applications', 'kglobalaccel']:
                text = (home / '.local/share' / directory / desktop).read_text()
                if str(home / '.local/bin' / (app + '-glass')) not in text:
                    raise RuntimeError('Shortcut bypasses launcher: ' + app)
        for name, binary in [('glass', home / '.local/opt/spectacle-glass/bin/spectacle'), ('system', Path('/usr/bin/spectacle'))]:
            text = (home / '.local/share/applications' / ('org.kde.spectacle-' + name + '-capture.desktop')).read_text()
            if str(binary) not in text or 'org.kde.KWin.ScreenShot2' not in text:
                raise RuntimeError('Screenshot authorization missing: ' + name)
        if panels.read_text() != 'Do not touch panel layout\n':
            raise RuntimeError('Unexpected panel modification')
        backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
        manifest = json.loads((backup / 'manifest.json').read_text())
        run(sys.executable, ROOT / 'scripts/install.py', '--restore', backup, '--home', home, '--no-live', stdout=subprocess.DEVNULL)
        for entry in manifest['entries']:
            target = home / entry['path']
            if entry['kind'] == 'absent' and (target.exists() or target.is_symlink()):
                raise RuntimeError('Rollback left installed file: ' + entry['path'])
        if (config / 'kwinrc').read_text() != old_kwin or panels.read_text() != 'Do not touch panel layout\n':
            raise RuntimeError('Rollback altered original configuration')
        print('Full installation, relocation, screenshot declarations and rollback passed.')

if __name__ == '__main__':
    main()
