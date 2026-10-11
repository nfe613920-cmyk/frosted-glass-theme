#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build matching Kate and KTextEditor releases for the opt-in glass launcher."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([str(x) for x in args], check=True)


def build_project(project, version, patch_name, target):
    patch = ROOT / 'patches' / patch_name
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()[:10]
    source = ROOT / 'build' / (project + '-' + version + '-' + digest)
    build = ROOT / 'build' / (project + '-build-' + version + '-' + digest)
    if not source.exists():
        run('git', 'clone', '--depth', '1', '--branch', 'v' + version, 'https://github.com/KDE/' + project + '.git', source)
    tag = subprocess.check_output(['git', '-C', str(source), 'describe', '--tags', '--exact-match', 'HEAD'], text=True).strip()
    if tag != 'v' + version:
        raise RuntimeError('Cached source release differs from requested version')
    if subprocess.run(['git', '-C', str(source), 'apply', '--reverse', '--check', str(patch)], capture_output=True).returncode:
        run('git', '-C', source, 'apply', '--check', patch)
        run('git', '-C', source, 'apply', patch)
    run('cmake', '-S', source, '-B', build, '-DBUILD_TESTING=OFF', '-DCMAKE_BUILD_TYPE=Release')
    targets = [target] if isinstance(target, str) else target
    run('cmake', '--build', build, '--target', *targets, '-j', '4')
    return build / 'bin'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kate-version', help='Exact installed Kate release')
    parser.add_argument('--ktexteditor-version', help='Exact installed KTextEditor release; default: Arch package version')
    args = parser.parse_args()
    kate = args.kate_version or subprocess.check_output(['kate', '--version'], text=True).strip().split()[-1]
    editor = args.ktexteditor_version or subprocess.check_output(['pacman', '-Q', 'ktexteditor'], text=True).split()[1].split('-')[0]
    for version in [kate, editor]:
        if not re.fullmatch(r'\d+\.\d+\.\d+', version):
            parser.error('Expected numeric major.minor.patch versions')
    editor_bin = build_project('ktexteditor', editor, 'ktexteditor-panel-glass.patch', 'KF6TextEditor')
    kate_bin = build_project('kate', kate, 'kate-panel-glass.patch', ['kate-bin', 'kwrite'])
    bundle = ROOT / 'build' / ('kate-bundle-' + kate)
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / 'bin').mkdir(parents=True)
    (bundle / 'lib').mkdir()
    shutil.copy2(kate_bin / 'kate', bundle / 'bin/kate')
    shutil.copy2(kate_bin / 'kwrite', bundle / 'bin/kwrite')
    shutil.copy2(kate_bin / ('libkateprivate.so.' + kate), bundle / 'lib' / ('libkateprivate.so.' + kate))
    shutil.copy2(editor_bin / 'libKF6TextEditor.so.6', bundle / 'lib/libKF6TextEditor.so.6')
    print('Kate bundle ready: ' + str(bundle))


if __name__ == '__main__':
    main()
