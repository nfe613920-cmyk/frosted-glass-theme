#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the opt-in Ark glass patch against the installed Ark release."""
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
    parser.add_argument('--ark-version', help='Exact installed Ark release')
    args = parser.parse_args()
    version = args.ark_version
    if not version:
        version = subprocess.check_output(['ark', '--version'], text=True).strip().split()[-1]
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        parser.error('Expected numeric major.minor.patch version')
    patch = ROOT / 'patches/ark-panel-glass.patch'
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()[:10]
    source = ROOT / 'build' / ('ark-' + version + '-' + digest)
    build = ROOT / 'build' / ('ark-build-' + version + '-' + digest)
    bundle = ROOT / 'build' / ('ark-bundle-' + version)
    if not source.exists():
        run('git', 'clone', '--depth', '1', '--branch', 'v' + version, 'https://github.com/KDE/ark.git', source)
    tag = subprocess.check_output(['git', '-C', str(source), 'describe', '--tags', '--exact-match', 'HEAD'], text=True).strip()
    if tag != 'v' + version:
        parser.error('Cached source release differs from requested version')
    if subprocess.run(['git','-C',str(source),'apply','--reverse','--check',str(patch)],capture_output=True).returncode:
        run('git', '-C', source, 'apply', '--check', patch)
        run('git', '-C', source, 'apply', patch)
    run('cmake', '-S', source, '-B', build, '-DBUILD_TESTING=OFF', '-DBUILD_DOC=OFF', '-DCMAKE_BUILD_TYPE=Release')
    run('cmake', '--build', build, '--target', 'ark', '-j', '4')
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / 'bin').mkdir(parents=True)
    (bundle / 'lib').mkdir()
    shutil.copy2(build / 'bin/ark', bundle / 'bin/ark')
    for name in ['libkerfuffle.so.' + version.split('.')[0]]:
        shutil.copy2(build / 'bin' / name, bundle / 'lib' / name)
    print('Ark bundle ready: ' + str(bundle))

if __name__ == '__main__':
    main()
