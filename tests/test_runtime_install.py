# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import tempfile
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
install = load('installer', ROOT / 'scripts/install.py')
launcher = load('launcher', ROOT / 'scripts/panelglass-app.py')
popup_launcher = load('popup_launcher', ROOT / 'runtime/popup-launcher.py')

class RuntimeInstallationTests(unittest.TestCase):
    def test_round_trip_preserves_actions_arguments_and_missing_apps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); home = root / 'new user'; home.mkdir()
            applications = root / 'applications'; applications.mkdir()
            binaries = root / 'bin'; binaries.mkdir()
            (binaries / 'systemsettings').touch()
            original = '[Desktop Entry]\nType=Application\nName=Settings\nExec=systemsettings kcm_colors\nTryExec=systemsettings\nDBusActivatable=true\nActions=VPN;\n\n[Desktop Action VPN]\nName=Import VPN\nExec=systemsettings kcm_networkmanagement --args VPN=%f\n'
            (applications / 'systemsettings.desktop').write_text(original)
            (applications / 'org.kde.kfontview.desktop').write_text('[Desktop Entry]\nExec=kfontview %U\n')
            target = home / '.local/share/applications/systemsettings.desktop'
            target.parent.mkdir(parents=True); target.write_text('personal previous launcher')
            bundle = root / 'bundle'; (bundle / 'plugins/generic').mkdir(parents=True)
            (bundle / 'plugins/generic/libpanelglass.so').write_bytes(b'bundle fixture')
            (bundle / 'PanelGlassTransparent.colors').write_text('palette fixture')
            private = home / '.local/opt/dolphin-glass/bin/dolphin'
            private.parent.mkdir(parents=True); private.touch()
            old_launcher = home / '.local/bin/dolphin-glass'
            old_launcher.parent.mkdir(parents=True); old_launcher.write_text('previous private launcher')
            backup = install.Backup(home)
            def write(path, text, mode=None):
                backup.save(path); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
                if mode: path.chmod(mode)
            def copy(source, dest):
                backup.save(dest); dest.parent.mkdir(parents=True, exist_ok=True); shutil.copytree(source, dest)
            entries = install.install_runtime(home, bundle, copy, write, applications, binaries)
            self.assertEqual(entries, ['systemsettings.desktop'])
            current = target.read_text()
            self.assertIn(str(home / '.local/bin/systemsettings-glass') + ' kcm_colors', current)
            self.assertIn(' --args VPN=%f', current)
            self.assertIn('Actions=VPN;', current)
            self.assertIn('DBusActivatable=false', current)
            self.assertFalse((home / '.local/bin/kfontview-glass').exists())
            self.assertFalse((home / '.local/share/color-schemes/PanelGlassTransparent.colors').exists())
            self.assertIn('popup-launcher.py', old_launcher.read_text())
            install.restore(home, backup.path)
            self.assertEqual(old_launcher.read_text(), 'previous private launcher')
            self.assertEqual(target.read_text(), 'personal previous launcher')
            self.assertFalse((home / '.local/opt/panelglass-runtime').exists())
            self.assertFalse((home / '.local/bin/systemsettings-glass').exists())

    def test_popup_environment_is_optional_and_keeps_existing_plugins(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            binary = home / 'private-app'; binary.touch()
            original = {'QT_PLUGIN_PATH': '/existing', 'QT_QPA_GENERIC_PLUGINS': 'other,panelglass', 'LANG': 'zh_CN.UTF-8'}
            with patch.object(popup_launcher.Path, 'home', return_value=home):
                self.assertEqual(popup_launcher.environment(binary, original), original)
                plugin = home / '.local/opt/panelglass-runtime/plugins/generic/libpanelglass.so'
                plugin.parent.mkdir(parents=True); plugin.touch()
                current = popup_launcher.environment(binary, original)
            self.assertEqual(current['PANEL_GLASS_POPUPS_ONLY'], '1')
            self.assertEqual(current['PANEL_GLASS_HOST'], str(binary.resolve()))
            self.assertEqual(current['QT_QPA_GENERIC_PLUGINS'], 'other,panelglass')
            self.assertTrue(current['QT_PLUGIN_PATH'].endswith(':/existing'))
            self.assertEqual(current['LANG'], original['LANG'])
            self.assertNotIn('PANEL_GLASS_POPUPS_ONLY', original)

    def test_symlink_host_and_existing_qt_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); binary = root / 'systemsettings'; binary.touch()
            info = root / 'kinfocenter'; info.symlink_to(binary)
            env = launcher.environment(info, root / 'runtime', {'QT_PLUGIN_PATH': '/existing', 'QT_QPA_GENERIC_PLUGINS': 'other,panelglass', 'LANG': 'zh_CN.UTF-8', 'PANEL_GLASS_POPUPS_ONLY': '1'})
            self.assertEqual(env['PANEL_GLASS_HOST'], str(binary))
            self.assertTrue(env['QT_PLUGIN_PATH'].endswith(':/existing'))
            self.assertEqual(env['QT_QPA_GENERIC_PLUGINS'], 'other,panelglass')
            self.assertEqual(env['LANG'], 'zh_CN.UTF-8')
            self.assertNotIn('PANEL_GLASS_POPUPS_ONLY', env)

if __name__ == '__main__': unittest.main()
