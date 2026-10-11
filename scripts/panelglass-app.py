#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Launch one explicitly enabled system Qt application with private glass styling."""
import os
from pathlib import Path
import sys

APPS = {'systemsettings', 'kinfocenter', 'plasma-discover', 'plasma-systemmonitor',
        'plasma-welcome', 'plasma-emojier', 'kcolorschemeeditor', 'keditfiletype',
        'kfontinst', 'kfontview', 'kmenuedit', 'knetattach', 'knewstuff-dialog6',
        'configure-printer', 'bluedevil-sendfile', 'bluedevil-wizard', 'plasma-print-queue',
        'fcitx5-config-qt', 'fcitx5-migrator', 'kbd-layout-viewer5', 'linguist6',
        'assistant6', 'qdbusviewer6', 'cmake-gui', 'kcmshell6'}

def environment(binary, runtime, environ):
    env = dict(environ)
    env.pop('PANEL_GLASS_POPUPS_ONLY', None)
    env['PANEL_GLASS_HOST'] = str(binary.resolve())
    env['PANEL_GLASS_SCHEME'] = str(runtime / 'PanelGlassTransparent.colors')
    plugin_path = str(runtime / 'plugins')
    env['QT_PLUGIN_PATH'] = plugin_path + (os.pathsep + env['QT_PLUGIN_PATH'] if env.get('QT_PLUGIN_PATH') else '')
    specs = [s for s in env.get('QT_QPA_GENERIC_PLUGINS', '').split(',') if s and s != 'panelglass']
    env['QT_QPA_GENERIC_PLUGINS'] = ','.join(specs + ['panelglass'])
    return env

def main():
    app = Path(sys.argv[0]).name.removesuffix('-glass')
    if app == 'panelglass-app':
        if len(sys.argv) < 2:
            raise SystemExit('Specify an enabled application')
        app = sys.argv.pop(1)
    if app not in APPS:
        raise SystemExit('Application is not enabled for Panel Glass')
    binary = Path('/usr/bin') / app
    runtime = Path.home() / '.local/opt/panelglass-runtime'
    if not binary.is_file():
        raise SystemExit(f'Application is not installed: {app}')
    if not (runtime / 'plugins/generic/libpanelglass.so').is_file():
        raise SystemExit('Build and install the Panel Glass runtime first')
    # Keep argv[0] as kinfocenter: it shares systemsettings' binary and selects its
    # mode from the invocation name. Preserve every original argument verbatim.
    os.execve(binary, [str(binary), *sys.argv[1:]], environment(binary, runtime, os.environ))

if __name__ == '__main__':
    main()
