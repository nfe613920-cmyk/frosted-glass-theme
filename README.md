# Frosted Glass Theme

保存 2026-10-10 的 KDE Plasma 毛玻璃桌面效果，重装系统后可按新用户名恢复。

包括顶部悬浮面板、应用菜单、底部 Dock、自定义 Dock 分隔器，以及 Konsole、Dolphin、Ark、Kate、KWrite、Spectacle 的整块毛玻璃窗口，并支持其他 KDE / Qt 6 工具的应用级适配。标题栏、工具栏和终端保持连续背景，保留原生窗口按钮，去掉分隔线、实体侧框和窗口阴影，并让模糊背景与圆角一致。

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

已在 Arch Linux、Plasma/Breeze 6.7.5、Qt 6.12.0、Konsole/Dolphin/Ark 26.08.2 上构建和使用。其他发行版需安装对应的 KDE/Qt 开发包。

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

关闭、最大化、最小化按钮依然由原生 Breeze 装饰提供。装饰补丁针对本仓库适配应用的窗口类名改变绘制，名单以补丁源码和下方应用说明为准，其他应用沿用同版本 Breeze 的原行为。升级 Breeze、KWin 或 Qt 后，请重新构建并安装匹配当前系统的插件。

## NetFloat

[NetFloat](https://github.com/nfe613920-cmyk/netfloat) 保持独立仓库，本仓库不复制其源码或二进制。它读取当前 Plasma 面板主题，因此安装这里的 Plasma 样式后可跟随同一毛玻璃效果。支持主题联动和悬浮面板边缘对齐的本地修改提交为 `91898a4`，请确认使用的 NetFloat 版本包含此提交。

## 文件结构

- `assets/plasma/`：面板和应用菜单样式、自定义 Dock 分隔器。
- `assets/konsole/`、`assets/color-schemes/`：终端配色、配置和工具栏样式。
- `layout/panels.js`：可选的面板布局重建脚本，使用当前会话分配的组件 ID。
- `patches/`：共享 Breeze 窗口装饰，以及 Dolphin、Ark 的背景补丁。
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

## 应用菜单图标

2026-10-12 将顶部左侧应用菜单换为 Arch Linux 图标。安装器保存图标，`--panels` 恢复布局时选用 `frosted-arch-white`。图标来自 [Arch Linux 官方 artwork 1.6](https://sources.archlinux.org/other/artwork/archlinux-artwork-1.6.tar.gz)，由 Thayer Williams 绘制，保留官方轮廓，改为与面板一致的纯白色。素材保留上游 CC BY-NC-SA 3.0 许可与 Arch 商标归属，详见 `docs/arch-artwork-authors.txt` 和 `LICENSES/CC-BY-NC-SA-3.0.txt`。

## Ark 整块毛玻璃（可选）

Ark 的标题栏、工具栏、列表表头、侧栏和欢迎页沿用同一块半透明背景。交替行只保留轻微的透明提示，欢迎页按钮使用半透明底色并保留悬停、按下和焦点反馈；窗口按钮和压缩、解压功能保持原生行为，通过 `ARK_PANEL_GLASS=1` 启用。

```sh
sudo pacman -S --needed ark kparts kio kcrash kwidgetsaddons kitemmodels ktextwidgets libarchive
python3 scripts/build-ark.py
python3 scripts/build-decoration.py
python3 scripts/install.py --dry-run --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --ark-bundle build/ark-bundle-26.08.2
python3 scripts/install.py --apply --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --ark-bundle build/ark-bundle-26.08.2
```

使用构建脚本打印的实际路径。可以同时传入 `--dolphin-bundle`；默认不改面板布局。安装器将程序和私有库保存到 `~/.local/opt/ark-glass`，用户应用菜单和压缩包文件关联沿用 `org.kde.ark.desktop`，调用 `~/.local/bin/ark-glass`。命令行也可使用这个启动器，支持 Ark 原有参数；直接执行 `/usr/bin/ark` 仍是发行版程序。

自定义主程序复用系统同版本 Ark 的 KPart 和压缩后端，因此必须与系统 Ark 版本匹配。升级 Ark、Breeze 或 KDE/Qt 后重新构建并安装。安装器自动备份 Ark 启动项和程序目录，可用同一个 `--restore` 恢复；不修改现有压缩包、文件关联首选顺序或 Ark 功能设置。

## Kate 整块毛玻璃（可选）

Kate 的标题栏、菜单、工具栏、标签页、侧栏、欢迎页和编辑区使用同一底色与透明度。`Panel Glass` 编辑主题保留 Breeze Dark 的语法高亮，行号区透明，当前行只保留轻微提示。KTextEditor 的缩略图和普通滚动条去掉独立实心背景，保留缩略图、书签标记与滚动行为。

```sh
sudo pacman -S --needed kate ktexteditor syntax-highlighting kparts kio karchive sonnet kauth editorconfig qt6-declarative qt6-speech
python3 scripts/build-kate.py
python3 scripts/build-decoration.py
python3 scripts/install.py --dry-run --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --kate-bundle build/kate-bundle-26.08.2
python3 scripts/install.py --apply --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --kate-bundle build/kate-bundle-26.08.2
```

以脚本实际输出路径为准。非 Arch 系统显式传入已安装的版本，例如 `python3 scripts/build-kate.py --kate-version 26.08.2 --ktexteditor-version 6.30.0`。构建器下载对应官方标签，只构建 Kate 主程序、私有库和 KTextEditor 库，不替换系统程序或框架。

用户目录中的 `~/.local/bin/kate-glass` 为新实例设置 `KATE_PANEL_GLASS=1` 并加载 `~/.local/opt/kate-glass/lib`，应用菜单和已有 Kate 文件关联使用这一入口。`/usr/bin/kate` 和其他使用 KTextEditor 的应用保持系统版本。安装不会把 Kate 设成所有文本文件的默认应用。

安装器备份 Kate 程序、启动项和编辑主题。升级 Kate、KTextEditor、Breeze 或 KDE/Qt 后重新构建匹配版本并安装。当前验证包括语法高亮显示、插入、撤销、重做、UTF-8 保存回读、分栏和欢迎页。

## KWrite 毛玻璃

`build-kate.py` 同时构建 KWrite。安装完整 Kate bundle 时自动安装 `kwrite-glass` 启动器和对应应用菜单项，与 Kate 共用私有库、编辑主题与原生毛玻璃标题栏。保留关闭按钮、工具栏和文件参数，不修改文本文件默认关联。KWrite 没有 Kate 的 `--new` 选项，启动器保留其原生启动方式。

## Spectacle 毛玻璃（可选）

截图主界面、图片标注窗口与设置对话框使用统一毛玻璃底色，保留窗口按钮、标注工具、缩放、截图倒计时与原有快捷键。截图本身保持原始内容。用户目录安装不会替换 `/usr/bin/spectacle`。

```sh
sudo pacman -S --needed spectacle kpipewire layer-shell-qt kquickimageeditor opencv tesseract qt6-multimedia qt6-wayland
python3 scripts/build-spectacle.py
python3 scripts/build-decoration.py
python3 scripts/install.py --dry-run --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --spectacle-bundle build/spectacle-bundle-6.7.5
python3 scripts/install.py --apply --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --spectacle-bundle build/spectacle-bundle-6.7.5
```

构建器使用当前 Spectacle 的官方发行标签，也可传入 `--version 6.7.5`。缺少的 Plasma Wayland 协议构建文件保存于本仓库的 build 缓存，不安装到系统。源码支持 OpenCV 4.7 或 5.0。升级 KDE/Qt 后重新构建并安装匹配版本。

安装同步应用菜单、所有桌面动作、全局快捷键 desktop 文件和两个 DBus 激活服务的入口；保留所有原始命令参数。注销后重新登录可刷新会话中已经缓存的快捷键入口，已有旧进程正常退出后新入口才会接管。

已验证后台截图导出、打开现有图片进入标注模式、标注界面显示、设置页、数值输入框箭头与键盘编辑。没有修改截图区域选择覆盖层或视频录制后端。自动检查数值控件可运行 `python3 scripts/check-spectacle-spin.py build/实际补丁源码目录`。

Spectacle 另有隐藏的 `org.kde.spectacle-glass-capture.desktop`，其 Exec 直接指向实际程序并声明截图接口。KWin 根据 `/proc` 中的程序路径查找授权，Python 启动脚本无法代替实际程序。同时保留系统程序的隐藏授权条目，让缓存的旧启动入口或显式 `/usr/bin/spectacle` 仍有原始截图权限。这些条目不增加应用菜单图标，卸载恢复时一并删除。

## 其他 KDE / Qt 6 应用

`runtime/` 提供按应用启动的 Qt GenericPlugin。它只在启动器声明的实际主程序中启用；信息中心的 OpenGL/Vulkan 检测程序及其他子进程保持原始行为。没有设置全局 `QT_PLUGIN_PATH`，没有降低文字、图标或整个窗口的透明度，也没有替换系统程序。

支持已安装的系统设置、信息中心、Discover、系统监视器、欢迎中心、表情选择器、菜单编辑器、配色编辑器、文件类型编辑器、字体查看/安装、网络文件夹、KNewStuff、蓝牙和打印工具，以及 Fcitx 配置/迁移、键盘布局查看、CMake GUI、Qt Linguist、Assistant、QDBusViewer 和 Qt Quick 设置 KCM。安装器只为本机存在的应用写入启动入口，保留原始参数、desktop actions 和语言设置。

Qt Widgets 主窗口绘制一次 `#1b2b37` / `145` 背景；工具栏、表头和侧栏去掉实体黑块。Qt Quick 使用相同玻璃底色，Kirigami 卡片保留浅色边框、悬停和按下反馈。系统设置侧栏的 QQuickWidget 使用透明合成顺序，避免被其他窗口遮挡后重绘花屏。窗口装饰仍保留关闭、最大化、最小化和缩放。

安装 Qt/KF 开发依赖后运行：

```sh
sudo pacman -S --needed qt6-declarative kirigami kcolorscheme kconfig kwindowsystem
python3 scripts/build-runtime.py
python3 scripts/build-decoration.py
python3 scripts/install.py --dry-run --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --runtime-bundle build/runtime-bundle
python3 scripts/install.py --apply --decoration build/decoration-6.7.5/bin/org.kde.breeze.konsoleglass-rounded.so --runtime-bundle build/runtime-bundle
```

可与 Dolphin、Ark、Kate、Spectacle 的 bundle 选项合并安装；不传 `--panels` 就不重建面板布局。从应用菜单打开即可使用新入口，终端启动时使用 `~/.local/bin/程序名-glass`，例如 `systemsettings-glass`、`plasma-discover-glass`、`fcitx5-config-qt-glass`。旧进程退出后再打开新窗口。升级 Qt、Kirigami、KWin/Breeze 后重新构建两种插件。

弹出菜单、右键菜单和级联子菜单使用同一透明底色、14px 圆角和圆角模糊区域，保留图标、快捷键、勾选项与原生键盘导航。已安装的 Dolphin、Konsole、Ark、Kate、KWrite、Spectacle 启动器会接入仅处理菜单的模式，保持各自主窗口的绘制方式。更新后需正常关闭原有应用进程再打开；已运行的进程不会热加载新插件。

功能检查：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check-runtime.py
```

已验证原生窗口启动、输入、按钮点击、数值编辑、停靠窗口构造、透明背景重复重绘、菜单圆角透明像素、勾选项和子菜单键盘导航、异步卡片加载及状态反馈；实际检查了系统设置/信息中心、软件中心、监控图表、欢迎中心、表情、菜单、字体查看、文件类型、网络向导、KNewStuff、Fcitx 配置及 Qt 开发工具界面。字体安装没有执行写入；打印配置无可用打印机，打印队列提示 CUPS 未运行；蓝牙发送提示 OBEX 服务不可用，未执行传输或配对。

本次适配保留配色编辑器的颜色预览、字体样张、文档及监控图表内容。不对 Qt Designer 的设计预览、QV4L2/QVidCap 视频画面或 Electron 自绘界面强制应用这套全局控件规则。
