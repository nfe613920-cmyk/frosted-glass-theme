# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/install.py'


class InstallationTests(unittest.TestCase):
    def test_dry_run_does_not_modify_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            plugin = home / 'fake.so'
            plugin.touch()
            cmd = [sys.executable, str(SCRIPT), '--dry-run', '--home', str(home),
                   '--decoration', str(plugin)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn('Dry run: would modify', result.stdout)
            self.assertFalse((home / '.config/kwinrc').exists())

    def test_live_installation_creates_backup_and_modifies_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.config').mkdir()
            kwinrc = home / '.config/kwinrc'
            kwinrc.write_text('[org.kde.kdecoration2]\nlibrary=old\n# preserve this comment\n')
            plugin = home / 'fake.so'
            plugin.touch()
            old_theme = home / '.local/share/plasma/desktoptheme/codex-frosted-glass'
            old_theme.parent.mkdir(parents=True)
            old_theme.write_text('old theme content')
            cmd = [sys.executable, str(SCRIPT), '--apply', '--home', str(home),
                   '--no-live', '--decoration', str(plugin)]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            current = kwinrc.read_text()
            self.assertIn('library=../../../../../../../../../../fake.so', current)
            self.assertIn('# preserve this comment', current)
            self.assertIn('blurEnabled=true', current)
            desktop = (home / '.local/share/applications/org.kde.konsole.desktop').read_text()
            self.assertIn(str(home / '.local/bin/konsole-glass').replace(' ', '\\ '), desktop)
            self.assertNotIn(str(Path.home()), desktop)
            self.assertTrue((home / '.local/share/konsole/PanelGlass.profile').exists())
            shortcut = home / '.local/share/kglobalaccel/org.kde.konsole.desktop'
            self.assertEqual(shortcut.read_text(), desktop)
            self.assertIn('X-KDE-Shortcuts=Ctrl+Alt+T', shortcut.read_text())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run([sys.executable, str(SCRIPT), '--restore', str(backup),
                            '--home', str(home), '--no-live'], capture_output=True, check=True)
            self.assertEqual(kwinrc.read_text(), '[org.kde.kdecoration2]\nlibrary=old\n# preserve this comment\n')
            self.assertEqual(old_theme.read_text(), 'old theme content')
            self.assertFalse((home / '.local/share/applications/org.kde.konsole.desktop').exists())
            self.assertFalse((home / '.local/share/konsole/PanelGlass.profile').exists())

    def test_dolphin_bundle_launchers_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            (bundle / 'bin').mkdir(parents=True)
            (bundle / 'bin/dolphin').touch()
            plugin = Path(tmp) / 'fake.so'
            plugin.touch()
            desktop = home / '.local/share/applications/org.kde.dolphin.desktop'
            desktop.parent.mkdir(parents=True)
            desktop.write_text('previous launcher')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--dolphin-bundle', str(bundle)], capture_output=True, check=True)
            self.assertIn(str(home / '.local/bin/dolphin-glass').replace(' ', '\\ '), desktop.read_text())
            shortcut = home / '.local/share/kglobalaccel/org.kde.dolphin.desktop'
            self.assertEqual(shortcut.read_text(), desktop.read_text())
            self.assertIn('X-KDE-Shortcuts=Meta+E', shortcut.read_text())
            service = (home / '.local/share/dbus-1/services/org.kde.dolphin.FileManager1.service').read_text()
            self.assertIn(str(home / '.local/bin/dolphin-glass'), service)
            self.assertTrue((home / '.local/opt/dolphin-glass/bin/dolphin').is_file())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            self.assertEqual(desktop.read_text(), 'previous launcher')
            self.assertFalse((home / '.local/share/kglobalaccel/org.kde.dolphin.desktop').exists())
            self.assertFalse((home / '.local/share/dbus-1/services/org.kde.dolphin.FileManager1.service').exists())
            self.assertFalse((home / '.local/opt/dolphin-glass').exists())

    def test_ark_bundle_launchers_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            (bundle / 'bin').mkdir(parents=True)
            (bundle / 'lib').mkdir(parents=True)
            (bundle / 'bin/ark').touch()
            (bundle / 'lib/libkerfuffle.so.26').touch()
            plugin = Path(tmp) / 'fake.so'
            plugin.touch()
            desktop = home / '.local/share/applications/org.kde.ark.desktop'
            desktop.parent.mkdir(parents=True)
            desktop.write_text('previous Ark launcher')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--ark-bundle', str(bundle)], capture_output=True, check=True)
            self.assertIn(str(home / '.local/bin/ark-glass').replace(' ', '\\ '), desktop.read_text())
            self.assertIn('%U', desktop.read_text())
            self.assertTrue((home / '.local/opt/ark-glass/lib/libkerfuffle.so.26').is_file())
            self.assertTrue((home / '.local/bin/ark-glass').stat().st_mode & 0o100)
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            self.assertEqual(desktop.read_text(), 'previous Ark launcher')
            self.assertFalse((home / '.local/opt/ark-glass').exists())
            self.assertFalse((home / '.local/bin/ark-glass').exists())

    def test_kate_and_kwrite_bundle_launchers_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            (bundle / 'bin').mkdir(parents=True)
            (bundle / 'lib').mkdir(parents=True)
            (bundle / 'bin/kate').touch()
            (bundle / 'bin/kwrite').touch()
            (bundle / 'lib/libKF6TextEditor.so.6').touch()
            plugin = Path(tmp) / 'fake.so'
            plugin.touch()
            theme = home / '.local/share/org.kde.syntax-highlighting/themes/PanelGlass.theme'
            for target in [home / '.local/share/applications/org.kde.kate.desktop',
                           home / '.local/share/applications/org.kde.kwrite.desktop',
                           theme]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('previous content')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--kate-bundle', str(bundle)], capture_output=True, check=True)
            self.assertIn(str(home / '.local/bin/kate-glass').replace(' ', '\\ '), desktop.read_text())
            self.assertIn('%U', desktop.read_text())
            self.assertNotIn('DBusActivatable=true', desktop.read_text())
            self.assertTrue((home / '.local/opt/kate-glass/lib/libKF6TextEditor.so.6').is_file())
            self.assertEqual(json.loads(theme.read_text())['metadata']['name'], 'Panel Glass')
            kwrite = home / '.local/share/applications/org.kde.kwrite.desktop'
            self.assertIn(str(home / '.local/bin/kwrite-glass').replace(' ', '\\ '), kwrite.read_text())
            self.assertNotIn('--new', (home / '.local/bin/kwrite-glass').read_text())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            self.assertEqual((home / '.local/share/applications/org.kde.kate.desktop').read_text(), 'previous content')
            self.assertEqual(kwrite.read_text(), 'previous content')
            self.assertEqual(theme.read_text(), 'previous content')
            self.assertFalse((home / '.local/opt/kate-glass').exists())
            self.assertFalse((home / '.local/bin/kate-glass').exists())
            self.assertFalse((home / '.local/bin/kwrite-glass').exists())

    def test_spectacle_bundle_launchers_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            (bundle / 'bin').mkdir(parents=True)
            (bundle / 'bin/spectacle').touch()
            plugin = Path(tmp) / 'fake.so'
            plugin.touch()
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--spectacle-bundle', str(bundle)], capture_output=True, check=True)
            desktop = home / '.local/share/applications/org.kde.spectacle.desktop'
            self.assertIn(str(home / '.local/bin/spectacle-glass').replace(' ', '\\ '), desktop.read_text())
            self.assertNotIn('Exec=/usr/bin/spectacle', desktop.read_text())
            self.assertNotIn('DBusActivatable=true', desktop.read_text())
            shortcut = home / '.local/share/kglobalaccel/org.kde.spectacle.desktop'
            self.assertEqual(shortcut.read_text(), desktop.read_text())
            auth = home / '.local/share/applications/org.kde.spectacle-glass-capture.desktop'
            self.assertIn(str(home / '.local/opt/spectacle-glass/bin/spectacle').replace(' ', '\\ '), auth.read_text())
            self.assertIn('X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2', auth.read_text())
            stock_auth = home / '.local/share/applications/org.kde.spectacle-system-capture.desktop'
            if Path('/usr/bin/spectacle').is_file():
                self.assertIn('Exec=/usr/bin/spectacle', stock_auth.read_text())
                self.assertIn('NoDisplay=true', stock_auth.read_text())
            self.assertIn('NoDisplay=true', auth.read_text())
            services = [home / '.local/share/dbus-1/services' / (name + '.service') for name in ['org.kde.Spectacle', 'org.kde.spectacle']]
            for service in services:
                self.assertIn(str(home / '.local/bin/spectacle-glass'), service.read_text())
                self.assertIn('--dbus', service.read_text())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            for target in [desktop, shortcut, auth, *services, home / '.local/opt/spectacle-glass', home / '.local/bin/spectacle-glass']:
                self.assertFalse(target.exists())
            if Path('/usr/bin/spectacle').is_file():
                self.assertFalse(stock_auth.exists())

    def test_restore_all_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.config').mkdir()
            (home / '.config/kwinrc').write_text('current')
            plugin = home / 'fake.so'
            plugin.touch()
            cmd = [sys.executable, str(SCRIPT), '--apply', '--home', str(home),
                   '--no-live', '--decoration', str(plugin)]
            subprocess.run(cmd, capture_output=True, check=True)
            self.assertTrue(any((home / '.local/state/frosted-glass-theme/backups').iterdir()))
            restore_script = ROOT / 'scripts/restore-all.py'
            subprocess.run([sys.executable, str(restore_script), '--home', str(home), '--no-live'],
                           capture_output=True, check=True)
            self.assertEqual((home / '.config/kwinrc').read_text(), 'current')

if __name__ == '__main__':
    unittest.main()
