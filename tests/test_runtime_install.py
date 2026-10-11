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
            backup = install.Backup(home)
            def write(path, text, mode=None):
                backup.save(path); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
                if mode: path.chmod(mode)
            def copy(source, dest):
                backup.save(dest); dest.parent.mkdir(parents=True, exist_ok=True); shutil.copytree(source, dest)
            entries = install.install_runtime(home, bundle, copy, write, applications, binaries)
            self.assertEqual(entries, ['systemsettings.desktop'])
            current = target.read_text()
            self.assertIn('"' + str(home / '.local/bin/systemsettings-glass') + '" kcm_colors', current)
            self.assertIn(' --args VPN=%f', current)
            self.assertIn('Actions=VPN;', current)
            self.assertIn('DBusActivatable=false', current)
            self.assertFalse((home / '.local/bin/kfontview-glass').exists())
            self.assertFalse((home / '.local/share/color-schemes/PanelGlassTransparent.colors').exists())
            install.restore(home, backup.path)
            self.assertEqual(target.read_text(), 'personal previous launcher')
            self.assertFalse((home / '.local/opt/panelglass-runtime').exists())
            self.assertFalse((home / '.local/bin/systemsettings-glass').exists())

    def test_symlink_host_and_existing_qt_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); binary = root / 'systemsettings'; binary.touch()
            info = root / 'kinfocenter'; info.symlink_to(binary)
            env = launcher.environment(info, root / 'runtime', {'QT_PLUGIN_PATH': '/existing', 'QT_QPA_GENERIC_PLUGINS': 'other,panelglass', 'LANG': 'zh_CN.UTF-8'})
            self.assertEqual(env['PANEL_GLASS_HOST'], str(binary))
            self.assertTrue(env['QT_PLUGIN_PATH'].endswith(':/existing'))
            self.assertEqual(env['QT_QPA_GENERIC_PLUGINS'], 'other,panelglass')
            self.assertEqual(env['LANG'], 'zh_CN.UTF-8')

if __name__ == '__main__': unittest.main()
