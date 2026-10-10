#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the opt-in Dolphin glass patch against the installed Dolphin release."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def run(*args):
    subprocess.run([str(x) for x in args], check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dolphin-version', help='Exact installed Dolphin release')
    args = parser.parse_args()
    version = args.dolphin_version
    if not version:
        version = subprocess.check_output(['dolphin', '--version'], text=True).strip().split()[-1]
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        parser.error('Expected numeric major.minor.patch version')
    patch = ROOT / 'patches/dolphin-panel-glass.patch'
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()[:10]
    source = ROOT / 'build' / ('dolphin-' + version + '-' + digest)
    build = ROOT / 'build' / ('dolphin-build-' + version + '-' + digest)
    bundle = ROOT / 'build' / ('dolphin-bundle-' + version)
    if not source.exists():
        run('git', 'clone', '--depth', '1', '--branch', 'v' + version, 'https://github.com/KDE/dolphin.git', source)
    tag = subprocess.check_output(['git', '-C', str(source), 'describe', '--tags', '--exact-match', 'HEAD'], text=True).strip()
    if tag != 'v' + version:
        parser.error('Cached source release differs from requested version')
    if subprocess.run(['git','-C',str(source),'apply','--reverse','--check',str(patch)],capture_output=True).returncode:
        run('git', '-C', source, 'apply', '--check', patch)
        run('git', '-C', source, 'apply', patch)
    run('cmake', '-S', source, '-B', build, '-DBUILD_TESTING=OFF', '-DCMAKE_BUILD_TYPE=Release')
    run('cmake', '--build', build, '--target', 'dolphin', '-j', '4')
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / 'bin').mkdir(parents=True)
    (bundle / 'lib').mkdir()
    shutil.copy2(build / 'bin/dolphin', bundle / 'bin/dolphin')
    for name in ['libdolphinprivate.so.6', 'libdolphinvcs.so.6']:
        shutil.copy2(build / 'bin' / name, bundle / 'lib' / name)
    print('Dolphin bundle ready: ' + str(bundle))

if __name__ == '__main__':
    main()
