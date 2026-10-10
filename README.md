# Frosted Glass Theme

保存 2026-10-10 的 KDE Plasma 毛玻璃桌面效果，重装系统后可按新用户名恢复。

包括顶部悬浮面板、应用菜单、底部 Dock、自定义 Dock 分隔器，以及 Konsole、Dolphin 的整块毛玻璃窗口。标题栏、工具栏和终端保持连续背景，保留原生窗口按钮，去掉分隔线、实体侧框和窗口阴影，并让模糊背景与圆角一致。

## 主题参数

| 项目 | 当前值 |
| --- | --- |
| 底色 | `#1b2b37` |
| 透明度 | `145/255`，约 56.86% |
| 圆角 | 14 px |
| KWin 模糊强度 | 15 |
| 顶部面板 | 悬浮、46 px、全宽、半透明 |
| 底部 Dock | 悬浮、72 px、内容自适应、居中、避让窗口 |

毛玻璃最终颜色随背景变化。本仓库不固定壁纸，也不包含壁纸文件。

## 重装后的完整恢复

仓库默认为私有；重装后先配置自己的 GitHub 认证，再克隆仓库。

已在 Arch Linux、Plasma/Breeze 6.7.5、Qt 6.12.0、Konsole/Dolphin 26.08.2 上构建和使用。其他发行版需安装对应的 KDE/Qt 开发包。

```sh
sudo pacman -S --needed git python cmake base-devel extra-cmake-modules qt6-base qt6-svg breeze kdecoration kcolorscheme kconfig kguiaddons ki18n kiconthemes kwindowsystem frameworkintegration kcmutils konsole
git clone https://github.com/nfe613920-cmyk/frosted-glass-theme.git
cd frosted-glass-theme
python3 scripts/build-decoration.py
```

构建脚本检测当前安装的 Breeze 版本，从 KDE 官方仓库下载对应发行标签并检查补丁。仅构建窗口装饰，不安装上游的面板、壁纸或系统样式。构建结束会打印 `.so` 的实际路径。

以 Breeze 6.7.5 为例：

```sh
python3 scripts/install.py --dry-run --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so
python3 scripts/install.py --apply --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so
```

安装只写入当前用户目录，自动备份被替换的文件。随后注销并重新登录，让 Plasma 加载主题和自定义组件；从应用菜单启动 Konsole。

若还需要重建截图中的顶部面板和底部 Dock，重新登录后运行：

```sh
python3 scripts/install.py --apply --panels
```

`--panels` 会替换现有的全部面板，恢复一套顶部面板与底部 Dock。这个选项只在你明确传入时执行；默认安装只应用主题，不改现有面板布局。没有安装 Chrome、Codex 或 Antigravity 时，可在 `layout/panels.js` 中替换相应的 Dock 启动器。

只恢复面板主题和 Konsole 基础透明配置时，可以省略 `--decoration`。完整的原生 Konsole 标题栏效果需要先构建装饰插件。

非 Arch 系统先查询已安装的 Breeze 版本，然后运行：

```sh
python3 scripts/build-decoration.py --breeze-version 6.7.5
```

## 撤销安装

安装结束会打印备份目录，位于 `~/.local/state/frosted-glass-theme/backups/`。恢复指定一次安装前的状态：

```sh
python3 scripts/install.py --restore ~/.local/state/frosted-glass-theme/backups/实际备份目录名
```

这会恢复该次安装替换的文件与设置，包括原窗口装饰。恢复面板布局后注销并重新登录。备份保存在本机，不上传到仓库。

## Konsole 启动方式

安装器在用户应用菜单中覆盖 Konsole 启动项，并安装 `~/.local/bin/konsole-glass`。它为新窗口加载工具栏样式。直接调用 `/usr/bin/konsole` 可能绕过这个样式；从终端启动相同效果时使用：

```sh
~/.local/bin/konsole-glass --separate
```

关闭、最大化、最小化按钮依然由原生 Breeze 装饰提供。装饰补丁仅在窗口类名包含 `konsole` 时改变绘制，其他应用沿用同版本 Breeze 的原行为。升级 Breeze、KWin 或 Qt 后，请重新构建并安装匹配当前系统的插件。

## NetFloat

[NetFloat](https://github.com/nfe613920-cmyk/netfloat) 保持独立仓库，本仓库不复制其源码或二进制。它读取当前 Plasma 面板主题，因此安装这里的 Plasma 样式后可跟随同一毛玻璃效果。支持主题联动和悬浮面板边缘对齐的本地修改提交为 `91898a4`，请确认使用的 NetFloat 版本包含此提交。

## 文件结构

- `assets/plasma/`：面板和应用菜单样式、自定义 Dock 分隔器。
- `assets/konsole/`、`assets/color-schemes/`：终端配色、配置和工具栏样式。
- `layout/panels.js`：可选的面板布局重建脚本，使用当前会话分配的组件 ID。
- `patches/`：Konsole 专用 Breeze 窗口装饰补丁。
- `scripts/`：构建、安装、备份和恢复。
- `tests/`：隔离目录中的安装/恢复测试，以及面板脚本模拟测试。
- `theme.json`：当前参数与已验证的软件版本。

仓库不包含访问令牌、MCP 配置、个人会话、屏幕输出 ID、绝对用户路径、已编译插件或完整桌面配置转储。

## 验证

```sh
python3 -m unittest discover -s tests -v
node tests/test-panels.cjs
```

参考：[Plasma 桌面脚本 API](https://develop.kde.org/docs/plasma/scripting/api/)、[Plasma 主题元素](https://develop.kde.org/docs/plasma/theme/theme-elements/)、[Breeze 源码](https://github.com/KDE/breeze)。许可证与上游来源见 [LICENSE](LICENSE) 和 [docs/upstream.md](docs/upstream.md)。

## Dolphin 整块毛玻璃（可选）

Dolphin 没有 Konsole 的原生透明背景设置，所以需要额外的源码补丁。这个版本把底色统一绘制在主窗口，侧栏、路径栏、标签栏、文件区、详细视图表头和状态栏保持透明，保留文件操作、窗口按钮、标签页及分栏功能。详细列表保留轻微透明的交替行提示。标题栏复用同一个 Breeze 装饰补丁。效果通过 `DOLPHIN_PANEL_GLASS=1` 启用。

安装当前 Dolphin 和开发依赖后构建：

```sh
sudo pacman -S --needed dolphin kio kparts kbookmarks solid kcompletion ktextwidgets knotifications kcrash kwidgetsaddons kcodecs kfilemetadata baloo baloo-widgets qt6-multimedia
python3 scripts/build-dolphin.py
python3 scripts/build-decoration.py
python3 scripts/install.py --dry-run --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --dolphin-bundle build/dolphin-bundle-26.08.2
python3 scripts/install.py --apply --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --dolphin-bundle build/dolphin-bundle-26.08.2
```

以构建脚本实际打印的路径为准。默认恢复不重建面板；需要恢复面板布局时另加 `--panels`。

自定义 Dolphin 安装在用户目录 `~/.local/opt/dolphin-glass`，主程序和私有库一起保存。应用菜单及 Dock 的 Dolphin 启动入口调用 `~/.local/bin/dolphin-glass`。已有窗口保留原有内容区外观；新开窗口使用毛玻璃版本。注销再登录后，文件管理器的 DBus 激活也使用该版本。直接执行 `/usr/bin/dolphin` 仍调用发行版程序。

升级 Dolphin 或 KDE/Qt 后重新构建并安装；版本不兼容时先迁移补丁。这里的编译产物不上传 Git，重装后在对应系统上重新构建。安装器的同一个备份也覆盖 Dolphin 的程序、启动入口和 DBus 服务配置，可用 `--restore` 恢复。

## 快捷键入口

安装器同时写入 `~/.local/share/applications/` 和 `~/.local/share/kglobalaccel/` 的启动项，确保 `Ctrl+Alt+T` 与 `Meta+E` 使用相同的毛玻璃启动命令。只覆盖应用菜单会漏掉 KDE 的全局快捷键入口。

当前 KDE 会话会缓存已经注册的启动命令，因此安装后注销再登录，让快捷键加载新入口。用户目录中的覆盖项会保留到下一次登录，也包含在安装器的回滚备份中。
