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
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            # Preserve actions and URL placeholders from the system desktop file.
            command = line[5:].split(maxsplit=1)
            line = 'Exec="' + escaped + '"' + (' ' + command[1] if len(command) > 1 else '')
        if line.startswith('TryExec='):
            line = 'TryExec=dolphin'
        if line.startswith('DBusActivatable='):
            line = 'DBusActivatable=false'
        lines.append(line)
    write(home / '.local/share/applications/org.kde.dolphin.desktop', '\n'.join(lines) + '\n')
    write(home / '.local/share/kglobalaccel/org.kde.dolphin.desktop', '\n'.join(lines) + '\n')
    service = '[D-BUS Service]\nName=org.freedesktop.FileManager1\nExec="' + escaped + '" --daemon\n'
    write(home / '.local/share/dbus-1/services/org.kde.dolphin.FileManager1.service', service)


def install_ark(home, bundle, copy, write):
    copy(bundle, home / '.local/opt/ark-glass')
    launcher = home / '.local/bin/ark-glass'
    write(launcher, (ROOT / 'scripts/ark-glass.py').read_text(), 0o755)
    desktop = Path('/usr/share/applications/org.kde.ark.desktop')
    text = desktop.read_text() if desktop.exists() else '[Desktop Entry]\nType=Application\nName=Ark\nIcon=ark\nExec=ark %U\n'
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec="' + escaped + '"' + (' ' + command[1] if len(command) > 1 else '')
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
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec="' + escaped + '"' + (' ' + command[1] if len(command) > 1 else '')
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
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec="' + escaped + '"' + (' ' + command[1] if len(command) > 1 else '')
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
    escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    lines = []
    for line in text.splitlines():
        if line.startswith('Exec='):
            command = line[5:].split(maxsplit=1)
            line = 'Exec="' + escaped + '"' + (' ' + command[1] if len(command) > 1 else '')
        if line.startswith('TryExec='):
            line = 'TryExec=spectacle'
        if line.startswith('DBusActivatable='):
            line = 'DBusActivatable=false'
        lines.append(line)
    write(home / '.local/share/applications/org.kde.spectacle.desktop', '\n'.join(lines) + '\n')

    write(home / '.local/share/kglobalaccel/org.kde.spectacle.desktop', '\n'.join(lines) + '\n')
    for name in ['org.kde.Spectacle', 'org.kde.spectacle']:
        service = '[D-BUS Service]\nName=' + name + '\nExec="' + escaped + '" --dbus\n'
        write(home / '.local/share/dbus-1/services' / (name + '.service'), service)


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
    parser.add_argument('--panels', action='store_true', help='Replace all existing panels with the saved top panel and bottom dock')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    live = not args.no_live and home == Path.home().resolve()
    if args.restore:
        restore(home, args.restore.expanduser().resolve())
        if live:
            reload_kwin()
        print('Backup restored. Log out and back in to reload Plasma layout and open new Konsole windows.')
        return
    if args.panels and not live and not args.dry_run:
        parser.error('--panels needs a live Plasma session; omit --no-live and use your current home')
    if args.decoration and not args.decoration.is_file():
        parser.error('Decoration plugin does not exist; build it first')
    if args.dolphin_bundle:
        if not args.decoration:
            parser.error('--dolphin-bundle requires --decoration for matching titlebar and corners')
        if not all((args.dolphin_bundle / name).is_file() for name in ['bin/dolphin', 'lib/libdolphinprivate.so.6', 'lib/libdolphinvcs.so.6']):
            parser.error('Dolphin bundle is incomplete; build it first')
    if args.ark_bundle:
        if not args.decoration:
            parser.error('--ark-bundle requires --decoration for matching titlebar and corners')
        if not (args.ark_bundle / 'bin/ark').is_file() or not list((args.ark_bundle / 'lib').glob('libkerfuffle.so.*')):
            parser.error('Ark bundle is incomplete; build it first')
    if args.spectacle_bundle:
        if not args.decoration or not (args.spectacle_bundle / 'bin/spectacle').is_file():
            parser.error('Spectacle requires a complete bundle and matching decoration')
    if args.kate_bundle:
        if not args.decoration:
            parser.error('--kate-bundle requires --decoration for matching titlebar and corners')
        if not (args.kate_bundle / 'bin/kate').is_file() or not (args.kate_bundle / 'lib/libKF6TextEditor.so.6').is_file() or not any(p.is_file() for p in (args.kate_bundle / 'lib').glob('libkateprivate.so.*')):
            parser.error('Kate bundle is incomplete; build it first')
    if args.panels and not args.dry_run:
        subprocess.run(['qdbus6', 'org.kde.plasmashell', '/PlasmaShell'], check=True, stdout=subprocess.DEVNULL)
    plan = [('Install Plasma style and Dock separator', '.local/share/plasma'),
            ('Install Konsole profile, palette and stylesheet', '.local/share/konsole'),
            ('Select saved Plasma style and Konsole profile', '.config'),
            ('Enable compositor blur at strength 15', '.config/kwinrc'),
            ('Configure Konsole launcher for a continuous glass toolbar', '.local/share/applications/org.kde.konsole.desktop')]
    if args.decoration:
        plan.append(('Install and select matching native Konsole glass decoration', '.local/lib/qt6/plugins/org.kde.kdecoration3'))
    if args.dolphin_bundle:
        plan.append(('Install opt-in Dolphin glass build and launcher', '.local/opt/dolphin-glass'))
    if args.ark_bundle:
        plan.append(('Install opt-in Ark glass build and launcher', '.local/opt/ark-glass'))
    if args.spectacle_bundle:
        plan.append(('Install Spectacle glass build, desktop and DBus launchers', '.local/opt/spectacle-glass'))
    if args.kate_bundle:
        plan.append(('Install opt-in Kate glass build, editor theme and launcher', '.local/opt/kate-glass'))
    if args.panels:
        plan.append(('Replace existing panels with saved layout', '.config/plasma-org.kde.plasma.desktop-appletsrc'))
    for message, path in plan:
        print(message + ': ' + str(home / path))
    if args.dry_run:
        return
    backup = Backup(home)

    def write(target, text, mode=None):
        backup.save(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        target.write_text(text)
        if mode:
            target.chmod(mode)

    def copy(source, target):
        backup.save(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        remove(target)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)

    def config(filename, group, key, value):
        target = home / '.config' / filename
        text = target.read_text() if target.exists() else ''
        write(target, set_key(text, group, key, value))

    try:
        for category in ['plasma/desktoptheme', 'plasma/plasmoids', 'konsole', 'color-schemes']:
            for source in (ROOT / 'assets' / category).iterdir():
                copy(source, home / '.local/share' / category / source.name)
        copy(ROOT / 'assets/icons/frosted-arch-white.svg', home / '.local/share/icons/hicolor/scalable/apps/frosted-arch-white.svg')
        config('plasmarc', ['Theme'], 'name', 'codex-frosted-glass')
        config('konsolerc', ['Desktop Entry'], 'DefaultProfile', 'PanelGlass.profile')
        config('konsolerc', ['UiSettings'], 'ColorScheme', 'KonsolePanelGlass')
        config('konsolerc', ['KonsoleWindow'], 'RemoveWindowTitleBarAndFrame', 'false')
        config('konsolerc', ['MainWindow'], 'MenuBar', 'Disabled')
        config('kwinrc', ['Plugins'], 'blurEnabled', 'true')
        config('kwinrc', ['Effect-blur'], 'BlurStrength', '15')
        if args.decoration:
            digest = hashlib.sha256(args.decoration.read_bytes()).hexdigest()[:12]
            plugin = home / '.local/lib/qt6/plugins/org.kde.kdecoration3' / ('org.kde.breeze.konsoleglass-' + digest + '.so')
            copy(args.decoration, plugin)
            # KWin prefixes its plugin namespace. A relative plugin ID resolves
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
                escaped = str(launcher).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
                line = 'Exec="' + escaped + '"' + suffix
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
        if args.panels:
            for name in ['plasma-org.kde.plasma.desktop-appletsrc', 'plasmashellrc']:
                backup.save(home / '.config' / name)
            script = (ROOT / 'layout/panels.js').read_text()
            subprocess.run(['qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', script], check=True)
        if live:
            subprocess.run(['kbuildsycoca6', '--noincremental'], check=True, stdout=subprocess.DEVNULL)
            reload_kwin()
    except Exception:
        restore(home, backup.path)
        print('Installation failed; saved files restored. If panel layout was running, log out and back in.', file=sys.stderr)
        raise
    print('Backup: ' + str(backup.path))
    print('Log out and back in to reload Plasma; open Konsole from its application launcher.')


if __name__ == '__main__':
    main()
