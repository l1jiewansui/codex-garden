# 第三方与美术来源

发布者：risu1。项目自身代码与素材尚未授予开源许可；本文件不改变各第三方原有许可。

- Electron 44.7.2：MIT；Chromium、Node.js 等所含组件许可随运行时的 LICENSE、LICENSES.chromium.html 提供。
- Python：PSF 许可。garden-bridge 与 garden-mcp 使用 PyInstaller 构建；PyInstaller 的 GPL 许可含运行时分发例外。所用解释器与构建工具许可见 licenses。
- MCP Python SDK 与所需依赖：固定版本及上游元数据见 dependencies.json；各发行包提供的许可证完整保留在 licenses/python 目录。
- 像素字体使用 SIL Open Font License，保留各字体作者版权与原始许可，见桌面应用 resources/app/assets/pixel-v04 下的许可文件；插件包中该路径位于 app 子目录。
- FrameRonin：MIT，固定版本的许可在素材目录保留。它用于素材处理，不作为对话数据服务运行。
- 默认三角色与原作像素工坊来自本项目存档人物，拆分为可编辑图层。可选的冒险像素画风来自下述 LPC 部件，沿用相应许可；蔬菜、地块及界面由本项目绘制并经过固定像素调色板处理。

本项目没有分发 Terraria 的游戏贴图、音乐、代码或商标。风格参考不代表 Terraria 官方合作或认可。公开宣传使用“二维像素桌面菜园”。

## Gardener and fantasy-plant artwork

The default classic library is composed from 37 semantic parts extracted or edited from the project's archived authored gardeners. The 33 idle/walk frames preserve the source pixels; 42 care frames re-register the heads on a shared pose rig. Face/scalp, front/back hair, hats, clothing and tools have separate ownership and material masks. Newly exposed scalp and hair behind hats are repaired derivatives, not recovered unseen original art. Source archive: archives/default-gardeners-rc11; processed native parts and provenance: resources/app/assets/pixel-classic. Editable native-part and material-mask projects are in art/classic and are compiled with the external LibreSprite v1.3 editor (GPL-2.0, https://github.com/LibreSprite/LibreSprite, commit cdb12a323ce5ec4fce3512bc6590a90228f15bb9). LibreSprite itself is not included in application or plugin packages. No LPC assets are used in classic sprites.

The optional adventure library composes 24 processed layers from Universal LPC Spritesheet Character Generator (https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator), pinned at 9bf06be193b053db256b2536824af426de046aa2. Adaptations: registered east-facing action rows, shared head/body mesh, material masks, garden-palette recoloring, head/nose selection and iris recoloring. Shared recipes ship in resources/app/assets/pixel-lpc/recipes.json. Attribution and original license texts ship in the adjacent CREDITS.md, CREDITS.json and license files; each part's creditId identifies its attribution. LPC-derived combined sprites are provided under CC-BY-SA 4.0.

The six fantasy plants under assets/pixel-fantasy are original pixel drawings, with fixed-root stage scaling and six-frame sway. No third-party game sprites or AI image service were used for these plants.
