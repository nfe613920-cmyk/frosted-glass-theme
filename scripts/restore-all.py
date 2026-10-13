#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build and optionally install every theme component. Panel layout is a separate opt-in."""
import argparse
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def numeric(value):
    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError("Expected a numeric major.minor.patch release: " + value)
    return value

def package_version(package):
    output = subprocess.check_output(['pacman', '-Q', package], text=True).split()[1]
    return numeric(output.rsplit('-', 1)[0].split(':')[-1])

def app_version(app):
    output = subprocess.check_output(['/usr/bin/' + app, '--version'], text=True)
    return numeric(output.split()[-1])

def plan(versions):
    build = ROOT / 'build'
    commands = []
    for component, options in [
        ('decoration', ['--breeze-version', versions['breeze']]),
        ('runtime', []),
        ('dolphin', ['--dolphin-version', versions['dolphin']]),
        ('ark', ['--ark-version', versions['ark']]),
        ('kate', ['--kate-version', versions['kate'], '--ktexteditor-version', versions['ktexteditor']]),
        ('spectacle', ['--version', versions['spectacle']]),
    ]:
        commands.append([sys.executable, str(ROOT / 'scripts' / ('build-' + component + '.py')), *options])
    install = [sys.executable, str(ROOT / 'scripts/install.py'), '--apply',
        '--decoration', str(build / ('decoration-' + versions['breeze']) / 'bin/org.kde.breeze.konsoleglass-rounded.so'),
        '--runtime-bundle', str(build / 'runtime-bundle'),
        '--dolphin-bundle', str(build / ('dolphin-bundle-' + versions['dolphin'])),
        '--ark-bundle', str(build / ('ark-bundle-' + versions['ark'])),
        '--kate-bundle', str(build / ('kate-bundle-' + versions['kate'])),
        '--spectacle-bundle', str(build / ('spectacle-bundle-' + versions['spectacle']))]
    return commands, install

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--dry-run', action='store_true', help='Print the complete plan without downloads or writes')
    action.add_argument('--build', action='store_true', help='Build all components without changing the desktop')
    action.add_argument('--apply', action='store_true', help='Build all components, then install with a local backup')
    parser.add_argument('--use-built', action='store_true', help='Skip builds and install existing bundles; requires --apply')
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--no-live', action='store_true', help='Skip desktop DBus calls (isolated installation verification)')
    for name in ['breeze', 'dolphin', 'ark', 'kate', 'ktexteditor', 'spectacle']:
        parser.add_argument('--' + name + '-version', help='Exact installed release; auto-detected on Arch')
    args = parser.parse_args()
    if args.use_built and not args.apply:
        parser.error('--use-built requires --apply')
    try:
        versions = {name: numeric(getattr(args, name + '_version')) if getattr(args, name + '_version')
            else package_version(name) if name in ['breeze', 'ktexteditor'] else app_version(name)
            for name in ['breeze', 'dolphin', 'ark', 'kate', 'ktexteditor', 'spectacle']}
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error('Install the documented dependencies or specify exact versions: ' + str(error))
    commands, install = plan(versions)
    install += ['--home', str(args.home.expanduser())]
    if args.no_live:
        install.append('--no-live')
    if args.dry_run:
        for command in [*commands, install]:
            print(shlex.join(command))
        print('Panel layout and NetFloat are restored separately; see README.')
        return
    if not args.use_built:
        for command in commands:
            subprocess.run(command, check=True)
    if args.apply:
        subprocess.run(install, check=True)

if __name__ == '__main__':
    main()
