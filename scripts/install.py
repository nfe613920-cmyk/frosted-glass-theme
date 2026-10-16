#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Install the saved theme with a full local backup. Never invoke sudo."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def set_key(text, group, key, value):
    """Update one KConfig key without rewriting other groups or comments."""
    header = '[' + ']['.join(group) + ']'
    lines = text.splitlines()
    if header not in lines:
        return text.rstrip() + '\n\n' + header + '\n' + key + '=' + str(value) + '\n'
    start = lines.index(header) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith('[')), len(lines))
    for i in range(start, end):
        if lines[i].startswith(key + '='):
            lines[i] = key + '=' + str(value)
            return '\n'.join(lines) + '\n'
    lines.insert(end, key + '=' + str(value))
    return '\n'.join(lines) + '\n'


class Backup:
    def __init__(self, home):
        self.home = home
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.path = home / '.local/state/frosted-glass-theme/backups' / stamp
        self.path.mkdir(parents=True, mode=0o700)
        self.entries = []
        self.saved = set()

    def save(self, target):
        relative = target.relative_to(self.home).as_posix()
        if relative in self.saved:
            return
        self.saved.add(relative)
        if target.is_symlink():
            entry = {'path': relative, 'kind': 'symlink', 'link': os.readlink(target)}
        elif target.exists():
            name = str(len(self.entries))
            saved = self.path / name
            if target.is_dir():
                shutil.copytree(target, saved, symlinks=True)
                kind = 'directory'
            else:
                shutil.copy2(target, saved)
                kind = 'file'
            entry = {'path': relative, 'kind': kind, 'saved': name}
        else:
            entry = {'path': relative, 'kind': 'absent'}
        self.entries.append(entry)
        manifest = self.path / 'manifest.json'
        manifest.write_text(json.dumps({'entries': self.entries}, indent=2))
        manifest.chmod(0o600)


def remove(target):
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)


def restore(home, backup_path):
    manifest = json.loads((backup_path / 'manifest.json').read_text())
    for entry in reversed(manifest['entries']):
        relative = Path(entry['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid backup path')
        target = home / relative
        remove(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry['kind'] == 'directory':
            shutil.copytree(backup_path / entry['saved'], target, symlinks=True)
        elif entry['kind'] == 'file':
            shutil.copy2(backup_path / entry['saved'], target)
        elif entry['kind'] == 'symlink':
            target.symlink_to(entry['link'])


def reload_kwin():
    subprocess.run(['qdbus6', 'org.kde.KWin', '/KWin', 'org.kde.KWin.reconfigure'], check=True)


def install_dolphin(home, bundle, copy, write):
    copy(bundle, home / '.local/opt/dolphin-glass')
    launcher = home / '.local/bin/dolphin-glass'
    write(launcher, (ROOT / 'scripts/dolphin-glass.py').read_text(), 0o755)
    desktop = Path('/usr/share/applications/org.kde.dolphin.desktop')
    text = desktop.read_text() if desktop.exists() else '[Desktop Entry]\nType=Application\nName=Dolphin\nIcon=system-file-manager\nExec=dolphin %u\n'
    text = set_key(text, ['Desktop Entry'], 'X-KDE-Shortcuts', 'Meta+E')
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            # Preserve actions and URL placeholders from the system desktop file.
            command = line[5:].split(maxsplit=1)
            line = 'Exec=' + escaped + (' ' + command[1] if len(command) > 1 else '')
        if line.startswith('TryExec='):
            line = 'TryExec=dolphin'
        if line.startswith('DBusActivatable='):
            line = 'DBusActivatable=false'
        lines.append(line)
    write(home / '.local/share/applications/org.kde.dolphin.desktop', '\n'.join(lines) + '\n')
    write(home / '.local/share/kglobalaccel/org.kde.dolphin.desktop', '\n'.join(lines) + '\n')
    service = '[D-BUS Service]\nName=org.freedesktop.FileManager1\nExec=' + escaped + ' --daemon\n'
    write(home / '.local/share/dbus-1/services/org.kde.dolphin.FileManager1.service', service)


def install_ark(home, bundle, copy, write):
    copy(bundle, home / '.local/opt/ark-glass')
    launcher = home / '.local/bin/ark-glass'
    write(launcher, (ROOT / 'scripts/ark-glass.py').read_text(), 0o755)
    desktop = Path('/usr/share/applications/org.kde.ark.desktop')
    text = desktop.read_text() if desktop.exists() else '[Desktop Entry]\nType=Application\nName=Ark\nIcon=ark\nExec=ark %U\n'
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec=' + escaped + (' ' + command[1] if len(command) > 1 else '')
        if line.startswith('TryExec='):
            line = 'TryExec=ark'
        if line.startswith('DBusActivatable='):
            line = 'DBusActivatable=false'
        lines.append(line)
    write(home / '.local/share/applications/org.kde.ark.desktop', '\n'.join(lines) + '\n')


def install_kate(home, bundle, copy, write):
    copy(bundle, home / '.local/opt/kate-glass')
    copy(ROOT / 'assets/editor-themes/PanelGlass.theme', home / '.local/share/org.kde.syntax-highlighting/themes/PanelGlass.theme')
    launcher = home / '.local/bin/kate-glass'
    write(launcher, (ROOT / 'scripts/kate-glass.py').read_text(), 0o755)
    desktop = Path('/usr/share/applications/org.kde.kate.desktop')
    text = desktop.read_text() if desktop.exists() else '[Desktop Entry]\nType=Application\nName=Kate\nIcon=kate\nExec=kate %U\n'
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec=' + escaped + (' ' + command[1] if len(command) > 1 else '')
        if line.startswith('TryExec='):
            line = 'TryExec=kate'
        if line.startswith('DBusActivatable='):
            line = 'DBusActivatable=false'
        lines.append(line)
    write(home / '.local/share/applications/org.kde.kate.desktop', '\n'.join(lines) + '\n')


def install_kwrite(home, bundle, copy, write):
    copy(bundle, home / '.local/opt/kate-glass')
    copy(ROOT / 'assets/editor-themes/PanelGlass.theme', home / '.local/share/org.kde.syntax-highlighting/themes/PanelGlass.theme')
    launcher = home / '.local/bin/kwrite-glass'
    write(launcher, (ROOT / 'scripts/kwrite-glass.py').read_text(), 0o755)
    desktop = Path('/usr/share/applications/org.kde.kwrite.desktop')
    text = desktop.read_text() if desktop.exists() else '[Desktop Entry]\nType=Application\nName=KWrite\nIcon=kwrite\nExec=kwrite %U\n'
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec=' + escaped + (' ' + command[1] if len(command) > 1 else '')
        if line.startswith('TryExec='):
            line = 'TryExec=kwrite'
        if line.startswith('DBusActivatable='):
            line = 'DBusActivatable=false'
        lines.append(line)
    write(home / '.local/share/applications/org.kde.kwrite.desktop', '\n'.join(lines) + '\n')


def install_spectacle(home, bundle, copy, write):
    copy(bundle, home / '.local/opt/spectacle-glass')
    launcher = home / '.local/bin/spectacle-glass'
    write(launcher, (ROOT / 'scripts/spectacle-glass.py').read_text(), 0o755)
    desktop = Path('/usr/share/applications/org.kde.spectacle.desktop')
    text = desktop.read_text() if desktop.exists() else '[Desktop Entry]\nType=Application\nName=Spectacle\nIcon=spectacle\nExec=spectacle %U\n'
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec=' + escaped + (' ' + command[1] if len(command) > 1 else '')
        if line.startswith('TryExec='):
            line = 'TryExec=spectacle'
        if line.startswith('DBusActivatable='):
            line = 'DBusActivatable=false'
        lines.append(line)
    write(home / '.local/share/applications/org.kde.spectacle.desktop', '\n'.join(lines) + '\n')

    write(home / '.local/share/kglobalaccel/org.kde.spectacle.desktop', '\n'.join(lines) + '\n')
    # KWin authorizes the actual process executable, not its wrapper or app ID.
    binary = home / '.local/opt/spectacle-glass/bin/spectacle'
    escaped_binary = str(binary).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
    authorization = ('[Desktop Entry]\nType=Application\nName=Spectacle Glass Capture\nNoDisplay=true\n'
                     'Exec=' + escaped_binary + '\n'
                     'X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2\n')
    write(home / '.local/share/applications/org.kde.spectacle-glass-capture.desktop', authorization)
    # The user desktop override hides the system desktop's original Exec too.
    # Keep the stock executable authorized for cached/explicit system launches.
    if Path('/usr/bin/spectacle').is_file():
        stock_authorization = authorization.replace('Spectacle Glass Capture', 'Spectacle System Capture').replace('Exec=' + escaped_binary, 'Exec=/usr/bin/spectacle')
        write(home / '.local/share/applications/org.kde.spectacle-system-capture.desktop', stock_authorization)

    for name in ['org.kde.Spectacle', 'org.kde.spectacle']:
        service = '[D-BUS Service]\nName=' + name + '\nExec=' + escaped + ' --dbus\n'
        write(home / '.local/share/dbus-1/services' / (name + '.service'), service)


RUNTIME_APPS = {
    'systemsettings.desktop': 'systemsettings',
    'kcm_fcitx5.desktop': 'systemsettings',
    'kcm_qtquicksettings.desktop': 'kcmshell6',
    'org.fcitx.fcitx5-config-qt.desktop': 'fcitx5-config-qt',
    'org.fcitx.fcitx5-migrator.desktop': 'fcitx5-migrator',
    'kbd-layout-viewer5.desktop': 'kbd-layout-viewer5',
    'linguist.desktop': 'linguist6',
    'assistant.desktop': 'assistant6',
    'qdbusviewer.desktop': 'qdbusviewer6',
    'cmake-gui.desktop': 'cmake-gui',
    'org.kde.vpnimport.desktop': 'systemsettings',
    'org.kde.kinfocenter.desktop': 'kinfocenter',
    'org.kde.discover.desktop': 'plasma-discover',
    'org.kde.discover.flatpak.desktop': 'plasma-discover',
    'org.kde.discover.snap.desktop': 'plasma-discover',
    'org.kde.discover.urlhandler.desktop': 'plasma-discover',
    'org.kde.plasma-systemmonitor.desktop': 'plasma-systemmonitor',
    'org.kde.plasma-welcome.desktop': 'plasma-welcome',
    'org.kde.plasma.emojier.desktop': 'plasma-emojier',
    'org.kde.kcolorschemeeditor.desktop': 'kcolorschemeeditor',
    'org.kde.keditfiletype.desktop': 'keditfiletype',
    'org.kde.kfontinst.desktop': 'kfontinst',
    'org.kde.kfontview.desktop': 'kfontview',
    'org.kde.kmenuedit.desktop': 'kmenuedit',
    'org.kde.knetattach.desktop': 'knetattach',
    'org.kde.knewstuff-dialog6.desktop': 'knewstuff-dialog6',
    'org.kde.ConfigurePrinter.desktop': 'configure-printer',
    'org.kde.bluedevilsendfile.desktop': 'bluedevil-sendfile',
    'org.kde.bluedevilwizard.desktop': 'bluedevil-wizard',
    'org.kde.plasma.printqueue.desktop': 'plasma-print-queue',
}


def install_runtime(home, bundle, copy, write, applications=Path('/usr/share/applications'), binaries=Path('/usr/bin')):
    copy(bundle, home / '.local/opt/panelglass-runtime')
    # Refresh existing private app launchers too: menu-only styling preserves
    # their individually patched main windows without adding a second layer.
    for app, directory in [('dolphin', 'dolphin-glass'), ('ark', 'ark-glass'),
                           ('kate', 'kate-glass'), ('kwrite', 'kate-glass'),
                           ('spectacle', 'spectacle-glass')]:
        if (home / '.local/opt' / directory / 'bin' / app).is_file():
            write(home / '.local/bin' / (app + '-glass'),
                  (ROOT / 'scripts' / (app + '-glass.py')).read_text(), 0o755)
    if (binaries / 'konsole').is_file():
        write(home / '.local/bin/konsole-glass', (ROOT / 'scripts/konsole-glass.py').read_text(), 0o755)
    source = (ROOT / 'scripts/panelglass-app.py').read_text()
    installed = []
    for name, app in RUNTIME_APPS.items():
        desktop = applications / name
        if not desktop.is_file() or not (binaries / app).is_file():
            continue
        launcher = home / '.local/bin' / (app + '-glass')
        write(launcher, source, 0o755)
        # Quote desktop Exec arguments using the freedesktop escaping rules.
        escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
        lines = []
        for line in desktop.read_text().splitlines():
            if line.startswith('Exec='):
                command = line[5:].split(maxsplit=1)
                line = 'Exec=' + escaped + (' ' + command[1] if len(command) > 1 else '')
            elif line.startswith('DBusActivatable='):
                line = 'DBusActivatable=false'
            lines.append(line)
        text = '\n'.join(lines) + '\n'
        write(home / '.local/share/applications' / name, text)
        # Desktop actions and any registered shortcuts use the same launcher.
        if (home / '.local/share/kglobalaccel' / name).exists() or (Path('/usr/share/kglobalaccel') / name).exists():
            write(home / '.local/share/kglobalaccel' / name, text)
        installed.append(name)
    return installed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true')
    action.add_argument('--apply', action='store_true')
    action.add_argument('--restore', type=Path, metavar='BACKUP_DIR')
    parser.add_argument('--home', type=Path, default=Path.home(), help='Target home directory (also usable for isolated tests)')
    parser.add_argument('--no-live', action='store_true', help='Skip desktop DBus calls')
    parser.add_argument('--decoration', type=Path, help='Built Breeze decoration plugin .so')
    parser.add_argument('--dolphin-bundle', type=Path, help='Optional bundle made by build-dolphin.py; requires the matching decoration')
    parser.add_argument('--ark-bundle', type=Path, help='Optional bundle made by build-ark.py; requires the matching decoration')
    parser.add_argument('--spectacle-bundle', type=Path, help='Optional Spectacle glass bundle; requires matching decoration')
    parser.add_argument('--kate-bundle', type=Path, help='Optional bundle made by build-kate.py; requires the matching decoration')
    parser.add_argument('--runtime-bundle', type=Path, help='Per-application Qt glass runtime made by build-runtime.py')
    parser.add_argument('--panels', action='store_true', help='Replace all existing panels with the saved top panel and bottom dock')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()

    if args.restore:
        restore(home, args.restore.resolve())
        if not args.no_live:
            reload_kwin()
        return

    backup = Backup(home)

    def write(path, text, mode=None):
        backup.save(path)
        if args.dry_run:
            print(f'Dry run: would write {path}')
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        if mode is not None:
            path.chmod(mode)

    def copy(source, destination):
        backup.save(destination)
        if args.dry_run:
            print(f'Dry run: would copy {source} -> {destination}')
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination, symlinks=True)
        else:
            shutil.copy2(source, destination)

    def config(name, group, key, value):
        file = home / '.config' / name
        backup.save(file)
        if args.dry_run:
            print(f'Dry run: would set {name} [{"][".join(group)}] {key}={value}')
            return
        text = file.read_text() if file.exists() else ''
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(set_key(text, group, key, value))

    if args.dry_run:
        print('Dry run: would modify kwinrc, desktop themes, and private launchers.')
        shutil.rmtree(backup.path)
        return

    try:
        theme = ROOT / 'assets/plasma-theme/codex-frosted-glass'
        copy(theme, home / '.local/share/plasma/desktoptheme/codex-frosted-glass')
        icons = ROOT / 'assets/icons/codex-glass-icons'
        copy(icons, home / '.local/share/icons/codex-glass-icons')
        konsole_profile = ROOT / 'assets/konsole-profiles/PanelGlass.profile'
        copy(konsole_profile, home / '.local/share/konsole/PanelGlass.profile')
        konsole_color = ROOT / 'assets/konsole-profiles/PanelGlass.colorscheme'
        copy(konsole_color, home / '.local/share/konsole/PanelGlass.colorscheme')

        config('plasmarc', ['Theme'], 'name', 'codex-frosted-glass')
        config('kdeglobals', ['Icons'], 'Theme', 'codex-glass-icons')
        config('kwinrc', ['Plugins'], 'blurEnabled', 'true')
        config('kwinrc', ['Plugins'], 'glideEnabled', 'true')
        config('kwinrc', ['Plugins'], 'magiclampEnabled', 'true')
        config('kwinrc', ['Plugins'], 'translucencyEnabled', 'true')
        config('kwinrc', ['Plugins'], 'wobblywindowsEnabled', 'true')
        config('kwinrc', ['Effect-translucency'], 'ComboboxPopups', '85')
        config('kwinrc', ['Effect-translucency'], 'Dialogs', '85')
        config('kwinrc', ['Effect-translucency'], 'Menus', '85')
        config('kwinrc', ['Effect-translucency'], 'MoveResize', '85')
        config('kwinrc', ['Windows'], 'InactiveTabsSkipTaskbar', 'true')
        config('kwinrc', ['Windows'], 'FocusPolicy', 'FocusFollowsMouse')
        config('kwinrc', ['Windows'], 'NextFocusPrefersMouse', 'true')
        config('kwinrc', ['org.kde.kdecoration2'], 'BorderSize', 'None')
        config('kwinrc', ['org.kde.kdecoration2'], 'BorderSizeAuto', 'false')
        config('kwinrc', ['org.kde.kdecoration2'], 'ShowOpaqueTitlebar', 'false')

        if args.decoration:
            plugin = args.decoration.resolve()
            # KWin accepts relative decoration plugin paths: use that to load
            # through the existing system Qt plugin directory without root writes.
            config('kwinrc', ['org.kde.kdecoration2'], 'library', '../' * 10 + str(plugin).lstrip('/'))
        launcher = home / '.local/bin/konsole-glass'
        source = (ROOT / 'scripts/konsole-glass.py').read_text()
        write(launcher, source, 0o755)
        desktop = Path('/usr/share/applications/org.kde.konsole.desktop')
        text = desktop.read_text() if desktop.exists() else '[Desktop Entry]\nType=Application\nName=Konsole\nIcon=utilities-terminal\nExec=konsole\n'
        text = set_key(text, ['Desktop Entry'], 'X-KDE-Shortcuts', 'Ctrl+Alt+T')
        lines = []
        for line in text.splitlines():
            if line.startswith('TryExec='):
                line = 'TryExec=konsole'
            if line.startswith('Exec='):
                suffix = ' --new-tab' if '--new-tab' in line else ' --separate'
                escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace(' ', '\\ ')
                line = 'Exec=' + escaped + suffix
            lines.append(line)
        write(home / '.local/share/applications/org.kde.konsole.desktop', '\n'.join(lines) + '\n')
        write(home / '.local/share/kglobalaccel/org.kde.konsole.desktop', '\n'.join(lines) + '\n')
        if args.dolphin_bundle:
            install_dolphin(home, args.dolphin_bundle, copy, write)
        if args.spectacle_bundle:
            install_spectacle(home, args.spectacle_bundle, copy, write)
        if args.ark_bundle:
            install_ark(home, args.ark_bundle, copy, write)
        if args.kate_bundle:
            install_kate(home, args.kate_bundle, copy, write)
            if (args.kate_bundle / 'bin/kwrite').is_file():
                install_kwrite(home, args.kate_bundle, copy, write)
        if args.runtime_bundle:
            install_runtime(home, args.runtime_bundle, copy, write)
        if args.panels:
            layout = ROOT / 'layout/panels.js'
            subprocess.run(['qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.loadScriptInInteractiveConsole', str(layout)], check=True)
        if not args.no_live:
            reload_kwin()
    except Exception:
        restore(home, backup.path)
        raise


if __name__ == '__main__':
    main()
