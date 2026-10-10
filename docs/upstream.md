# 上游来源与补丁说明

Plasma 样式来自本机 KDE 默认样式，保留 KDE Visual Design Group 作者与 LGPL 元数据。仓库保存当前使用的全部主题资产，以免系统默认主题升级后改变效果；主要定制在面板、对话框、应用菜单背景及 `plasmarc` 的模糊配置。

Konsole ANSI 配色源自 [KDE Konsole](https://github.com/KDE/konsole)，背景色、透明度和模糊开关经过定制。

窗口装饰补丁基于 [Breeze v6.7.5](https://github.com/KDE/breeze/tree/v6.7.5)，基准提交 `ca217f12ce16a28e601c78b7f2fdceca586725b2`。上游文件的版权头和许可证保持不变。

Konsole 和 Dolphin 特殊分支完成以下处理：

1. 原生标题栏底色只绘制一次，避免半透明底色叠加。
2. 标题栏使用与终端、工具栏相同的底色与透明度。
3. 标题栏保持透明，并向 KWin 提供模糊区域。
4. 原生描边、实体侧框和阴影不参与 这两个应用的绘制，边缘缩放区域仍保留。
5. 统一顶部和底部 14 px 圆角，让 KWin 的模糊输出也按圆角裁剪，消除圆角外的直角背景。
6. 原生窗口按钮、移动、缩放、最大化逻辑继续使用 Breeze。

补丁针对当前窗口类名识别 Konsole 和 Dolphin。插件作为同版本 Breeze 的替代装饰加载，其他窗口不进入上述特殊分支。它不修改 Plasma 面板代码。

构建器会匹配已安装的 Breeze 版本。若较新版本无法通过 `git apply --check` 或 CMake 构建，先迁移补丁；构建失败时不会安装旧 ABI 的二进制或更改桌面。

Dolphin 补丁基于 [Dolphin v26.08.2](https://github.com/KDE/dolphin/tree/v26.08.2)，基准提交 `f19f070e7dc140213a2c6dd5d11f26122c89e1a0`。修改的 Dolphin 源文件保持 GPL-2.0-or-later 许可证，构建器下载同版本上游源码并应用补丁。
