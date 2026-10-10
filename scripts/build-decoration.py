#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build native window decoration against the currently installed Breeze version."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*argv):
    subprocess.run([str(x) for x in argv], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--breeze-version', help='Exact installed Breeze release; detected with pacman on Arch')
    args = p.parse_args()
    version = args.breeze_version
    if not version:
        try:
            value = subprocess.check_output(['pacman', '-Q', 'breeze'], text=True).split()[1]
            version = value.rsplit('-', 1)[0].split(':')[-1]
        except (FileNotFoundError, subprocess.CalledProcessError):
            p.error('Specify the exact installed version with --breeze-version (tested: 6.7.5)')
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        p.error('Version must be numeric major.minor.patch')
    source = ROOT / 'build' / ('breeze-' + version)
    build = ROOT / 'build' / ('decoration-' + version)
    if not source.exists():
        run('git', 'clone', '--depth', '1', '--branch', 'v' + version, 'https://github.com/KDE/breeze.git', source)
    current = subprocess.check_output(['git', '-C', str(source), 'describe', '--tags', '--exact-match', 'HEAD'], text=True).strip()
    if current != 'v' + version:
        p.error('Cached source version differs from requested version')
    patch = ROOT / 'patches/breeze-konsole-glass.patch'
    already = subprocess.run(['git', '-C', str(source), 'apply', '--reverse', '--check', str(patch)], capture_output=True).returncode == 0
    if not already:
        run('git', '-C', source, 'apply', '--check', patch)
        run('git', '-C', source, 'apply', patch)
    run('cmake', '-S', source, '-B', build, '-DBUILD_QT5=OFF', '-DBUILD_TESTING=OFF', '-DBUILD_CURSOR=OFF', '-DBUILD_WITH_QTQUICK=OFF', '-DWITH_WALLPAPERS=OFF', '-DCMAKE_BUILD_TYPE=Release')
    run('cmake', '--build', build, '--target', 'breezedecoration', '-j', '4')
    print('Decoration ready: ' + str(build / 'bin/org.kde.breeze.konsoleglass-rounded.so'))


if __name__ == '__main__':
    main()
