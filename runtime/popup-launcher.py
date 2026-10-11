# SPDX-License-Identifier: MIT
"""Attach menu-only glass to an already styled private application."""
from pathlib import Path
import os

def environment(binary, env):
    runtime = Path.home() / '.local/opt/panelglass-runtime'
    if not (runtime / 'plugins/generic/libpanelglass.so').is_file():
        return env
    env = dict(env)
    env['PANEL_GLASS_HOST'] = str(Path(binary).resolve())
    env['PANEL_GLASS_POPUPS_ONLY'] = '1'
    plugins = str(runtime / 'plugins')
    env['QT_PLUGIN_PATH'] = plugins + (os.pathsep + env['QT_PLUGIN_PATH'] if env.get('QT_PLUGIN_PATH') else '')
    specs = [s for s in env.get('QT_QPA_GENERIC_PLUGINS', '').split(',') if s and s != 'panelglass']
    env['QT_QPA_GENERIC_PLUGINS'] = ','.join(specs + ['panelglass'])
    return env
