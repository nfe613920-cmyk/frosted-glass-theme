#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the installed Spectacle release with the opt-in glass patch."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([str(x) for x in args], check=True)


def checkout(project, version, source):
    if not source.exists():
        run('git', 'clone', '--depth', '1', '--branch', 'v' + version, 'https://github.com/KDE/' + project + '.git', source)
    actual = subprocess.check_output(['git', '-C', str(source), 'describe', '--tags', '--exact-match', 'HEAD'], text=True).strip()
    if actual != 'v' + version:
        raise RuntimeError('Source tag differs from requested release')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', help='Exact installed Spectacle version')
    args = parser.parse_args()
    version = args.version or subprocess.check_output(['spectacle', '--version'], text=True).split()[-1]
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        parser.error('Expected major.minor.patch version')
    patch = ROOT / 'patches/spectacle-panel-glass.patch'
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()[:10]
    source = ROOT / 'build' / ('spectacle-' + version + '-' + digest)
    build = ROOT / 'build' / ('spectacle-build-' + version + '-' + digest)
    checkout('spectacle', version, source)
    if subprocess.run(['git', '-C', str(source), 'apply', '--reverse', '--check', str(patch)], capture_output=True).returncode:
        run('git', '-C', source, 'apply', '--check', patch)
        run('git', '-C', source, 'apply', patch)
    # Protocol headers are build-only; keep them inside the repository cache.
    protocol = ROOT / 'build/plasma-wayland-protocols-1.20.0'
    protocol_build = ROOT / 'build/plasma-wayland-protocols-build'
    deps = ROOT / 'build/spectacle-deps'
    checkout('plasma-wayland-protocols', '1.20.0', protocol)
    run('cmake', '-S', protocol, '-B', protocol_build, '-DCMAKE_INSTALL_PREFIX=' + str(deps))
    run('cmake', '--install', protocol_build)
    run('cmake', '-S', source, '-B', build, '-DBUILD_TESTING=OFF', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_PREFIX_PATH=' + str(deps))
    run('cmake', '--build', build, '--target', 'spectacle', '-j', '4')
    bundle = ROOT / 'build' / ('spectacle-bundle-' + version)
    (bundle / 'bin').mkdir(parents=True, exist_ok=True)
    shutil.copy2(build / 'bin/spectacle', bundle / 'bin/spectacle')
    print('Spectacle bundle ready: ' + str(bundle))


if __name__ == '__main__':
    main()
