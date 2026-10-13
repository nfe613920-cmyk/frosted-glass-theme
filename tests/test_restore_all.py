# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('restore_all', ROOT / 'scripts/restore-all.py')
restore = importlib.util.module_from_spec(spec); spec.loader.exec_module(restore)
VERSIONS = {'breeze':'6.7.5', 'dolphin':'26.08.2', 'ark':'26.08.2',
            'kate':'26.08.2', 'ktexteditor':'6.30.0', 'spectacle':'6.7.5'}

class FullRestoreTests(unittest.TestCase):
    def test_complete_plan_has_all_bundles_and_no_implicit_panels(self):
        commands, install = restore.plan(VERSIONS)
        self.assertEqual(len(commands), 6)
        self.assertIn('build-runtime.py', Path(commands[1][1]).name)
        for flag in ['--decoration', '--runtime-bundle', '--dolphin-bundle', '--ark-bundle', '--kate-bundle', '--spectacle-bundle']:
            self.assertIn(flag, install)
            target = Path(install[install.index(flag)+1])
            self.assertTrue(target.is_relative_to(ROOT / 'build'))
        self.assertNotIn('--panels', install)

    def test_dry_run_requires_no_installed_kde_when_versions_supplied(self):
        args = [sys.executable, str(ROOT / 'scripts/restore-all.py'), '--dry-run']
        for name, version in VERSIONS.items():
            args += ['--'+name+'-version', version]
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        self.assertIn('--runtime-bundle', result.stdout)
        self.assertIn('--spectacle-bundle', result.stdout)
        self.assertNotIn('--panels', result.stdout)

    def test_version_cannot_be_a_path_or_git_option(self):
        for value in ['../source', '--branch=main', '6.7', '6.7.5;touch nope']:
            with self.assertRaises(ValueError): restore.numeric(value)
