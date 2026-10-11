# SPDX-License-Identifier: MIT
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/install.py'
spec = importlib.util.spec_from_file_location('theme_install', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallationTests(unittest.TestCase):
    def test_install_restore_and_preserve_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'another user'
            config = home / '.config'
            config.mkdir(parents=True)
            old = '# preserve this comment\n[Plugins]\nblurEnabled=false\notherEffect=true\n\n[Desktops]\nNumber=3\n'
            (config / 'kwinrc').write_text(old)
            old_theme = home / '.local/share/plasma/desktoptheme/codex-frosted-glass'
            old_theme.mkdir(parents=True)
            (old_theme / 'original.txt').write_text('previous theme')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            result = subprocess.run(cmd + ['--apply'], capture_output=True, text=True, check=True)
            current = (config / 'kwinrc').read_text()
            self.assertIn('otherEffect=true', current)
            self.assertIn('Number=3', current)
            self.assertIn('# preserve this comment', current)
            self.assertIn('blurEnabled=true', current)
            desktop = (home / '.local/share/applications/org.kde.konsole.desktop').read_text()
            self.assertIn(str(home / '.local/bin/konsole-glass'), desktop)
            self.assertNotIn(str(Path.home()), desktop)
            self.assertTrue((home / '.local/share/konsole/PanelGlass.profile').exists())
            shortcut = home / '.local/share/kglobalaccel/org.kde.konsole.desktop'
            self.assertEqual(shortcut.read_text(), desktop)
            self.assertIn('X-KDE-Shortcuts=Ctrl+Alt+T', shortcut.read_text())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            self.assertIn(str(backup), result.stdout)
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            self.assertEqual((config / 'kwinrc').read_text(), old)
            self.assertEqual((old_theme / 'original.txt').read_text(), 'previous theme')
            self.assertFalse((home / '.local/share/konsole/PanelGlass.profile').exists())
            self.assertFalse(shortcut.exists())

    def test_dolphin_bundle_install_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            for name in ['bin/dolphin', 'lib/libdolphinprivate.so.6', 'lib/libdolphinvcs.so.6']:
                target = bundle / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'bundle fixture')
            plugin = Path(tmp) / 'decoration.so'
            plugin.write_bytes(b'plugin fixture')
            desktop = home / '.local/share/applications/org.kde.dolphin.desktop'
            desktop.parent.mkdir(parents=True)
            desktop.write_text('previous launcher')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--dolphin-bundle', str(bundle)], capture_output=True, check=True)
            self.assertIn(str(home / '.local/bin/dolphin-glass'), desktop.read_text())
            shortcut = home / '.local/share/kglobalaccel/org.kde.dolphin.desktop'
            self.assertEqual(shortcut.read_text(), desktop.read_text())
            self.assertIn('X-KDE-Shortcuts=Meta+E', shortcut.read_text())
            service = home / '.local/share/dbus-1/services/org.kde.dolphin.FileManager1.service'
            self.assertIn('--daemon', service.read_text())
            self.assertTrue((home / '.local/opt/dolphin-glass/bin/dolphin').is_file())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            self.assertEqual(desktop.read_text(), 'previous launcher')
            self.assertFalse(service.exists())
            self.assertFalse(shortcut.exists())
            self.assertFalse((home / '.local/opt/dolphin-glass').exists())

    def test_ark_bundle_install_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            for name in ['bin/ark', 'lib/libkerfuffle.so.26']:
                target = bundle / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'bundle fixture')
            plugin = Path(tmp) / 'decoration.so'
            plugin.write_bytes(b'plugin fixture')
            desktop = home / '.local/share/applications/org.kde.ark.desktop'
            desktop.parent.mkdir(parents=True)
            desktop.write_text('previous Ark launcher')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--ark-bundle', str(bundle)], capture_output=True, check=True)
            self.assertIn(str(home / '.local/bin/ark-glass'), desktop.read_text())
            self.assertIn('%U', desktop.read_text())
            self.assertTrue((home / '.local/opt/ark-glass/lib/libkerfuffle.so.26').is_file())
            self.assertTrue((home / '.local/bin/ark-glass').stat().st_mode & 0o100)
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            self.assertEqual(desktop.read_text(), 'previous Ark launcher')
            self.assertFalse((home / '.local/opt/ark-glass').exists())
            self.assertFalse((home / '.local/bin/ark-glass').exists())

    def test_kate_bundle_theme_and_launcher_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            for name in ['bin/kate', 'bin/kwrite', 'lib/libkateprivate.so.26.08.2', 'lib/libKF6TextEditor.so.6']:
                target = bundle / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'bundle fixture')
            plugin = Path(tmp) / 'decoration.so'
            plugin.write_bytes(b'plugin fixture')
            desktop = home / '.local/share/applications/org.kde.kate.desktop'
            theme = home / '.local/share/org.kde.syntax-highlighting/themes/PanelGlass.theme'
            for target in [desktop, theme]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('previous content')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--kate-bundle', str(bundle)], capture_output=True, check=True)
            self.assertIn(str(home / '.local/bin/kate-glass'), desktop.read_text())
            self.assertIn('%U', desktop.read_text())
            self.assertNotIn('DBusActivatable=true', desktop.read_text())
            self.assertTrue((home / '.local/opt/kate-glass/lib/libKF6TextEditor.so.6').is_file())
            self.assertEqual(json.loads(theme.read_text())['metadata']['name'], 'Panel Glass')
            kwrite = home / '.local/share/applications/org.kde.kwrite.desktop'
            self.assertIn(str(home / '.local/bin/kwrite-glass'), kwrite.read_text())
            self.assertNotIn('--new', (home / '.local/bin/kwrite-glass').read_text())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            self.assertEqual(desktop.read_text(), 'previous content')
            self.assertEqual(theme.read_text(), 'previous content')
            self.assertFalse((home / '.local/opt/kate-glass').exists())
            self.assertFalse((home / '.local/bin/kate-glass').exists())
            self.assertFalse(kwrite.exists())
            self.assertFalse((home / '.local/bin/kwrite-glass').exists())

    def test_spectacle_bundle_launchers_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'new user'
            bundle = Path(tmp) / 'bundle'
            binary = bundle / 'bin/spectacle'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'bundle fixture')
            plugin = Path(tmp) / 'decoration.so'
            plugin.write_bytes(b'plugin fixture')
            cmd = [sys.executable, str(SCRIPT), '--home', str(home), '--no-live']
            subprocess.run(cmd + ['--apply', '--decoration', str(plugin), '--spectacle-bundle', str(bundle)], capture_output=True, check=True)
            desktop = home / '.local/share/applications/org.kde.spectacle.desktop'
            self.assertIn(str(home / '.local/bin/spectacle-glass'), desktop.read_text())
            self.assertNotIn('Exec=/usr/bin/spectacle', desktop.read_text())
            self.assertNotIn('DBusActivatable=true', desktop.read_text())
            shortcut = home / '.local/share/kglobalaccel/org.kde.spectacle.desktop'
            self.assertEqual(shortcut.read_text(), desktop.read_text())
            auth = home / '.local/share/applications/org.kde.spectacle-glass-capture.desktop'
            self.assertIn(str(home / '.local/opt/spectacle-glass/bin/spectacle'), auth.read_text())
            self.assertIn('X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2', auth.read_text())
            self.assertIn('NoDisplay=true', auth.read_text())
            services = [home / '.local/share/dbus-1/services' / (name + '.service') for name in ['org.kde.Spectacle', 'org.kde.spectacle']]
            for service in services:
                self.assertIn('--dbus', service.read_text())
                self.assertNotIn('SystemdService', service.read_text())
            backup = next((home / '.local/state/frosted-glass-theme/backups').iterdir())
            subprocess.run(cmd + ['--restore', str(backup)], capture_output=True, check=True)
            for target in [desktop, shortcut, auth, *services, home / '.local/opt/spectacle-glass', home / '.local/bin/spectacle-glass']:
                self.assertFalse(target.exists())

    def test_kate_rejects_incomplete_bundle_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'empty'
            plugin = Path(tmp) / 'decoration.so'
            plugin.write_bytes(b'plugin fixture')
            for flags in [[], ['--decoration', str(plugin)]]:
                result = subprocess.run([sys.executable, str(SCRIPT), '--home', str(home), '--no-live', '--apply', '--kate-bundle', tmp] + flags, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(home.exists())

    def test_ark_rejects_invalid_bundle_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'empty'
            plugin = Path(tmp) / 'decoration.so'
            plugin.write_bytes(b'plugin fixture')
            for flags in [[], ['--decoration', str(plugin)]]:
                result = subprocess.run([sys.executable, str(SCRIPT), '--home', str(home), '--no-live', '--apply', '--ark-bundle', tmp] + flags, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(home.exists())

    def test_dolphin_rejects_missing_decoration_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'empty'
            result = subprocess.run([sys.executable, str(SCRIPT), '--home', str(home), '--no-live', '--apply', '--dolphin-bundle', tmp], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(home.exists())

    def test_dry_run_has_no_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'empty home'
            subprocess.run([sys.executable, str(SCRIPT), '--home', str(home), '--no-live', '--dry-run'], capture_output=True, check=True)
            self.assertFalse(home.exists())

    def test_invalid_plugin_rejected_before_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'empty'
            result = subprocess.run([sys.executable, str(SCRIPT), '--home', str(home), '--no-live', '--apply', '--decoration', '/missing/plugin.so'], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(home.exists())

    def test_backup_restores_symlink_without_touching_referent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            original = home / 'original'
            original.write_text('keep me')
            link = home / 'target'
            link.symlink_to(original)
            backup = module.Backup(home)
            backup.save(link)
            link.unlink()
            link.write_text('replacement')
            module.restore(home, backup.path)
            self.assertTrue(link.is_symlink())
            self.assertEqual(original.read_text(), 'keep me')

    def test_corrupt_backup_cannot_escape_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'home'
            backup = Path(tmp) / 'backup'
            backup.mkdir()
            (backup / 'manifest.json').write_text(json.dumps({'entries': [{'path': '../outside', 'kind': 'absent'}]}))
            with self.assertRaises(ValueError):
                module.restore(home, backup)


if __name__ == '__main__':
    unittest.main()
