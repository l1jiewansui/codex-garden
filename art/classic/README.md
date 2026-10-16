# 原作像素园丁

用 [LibreSprite](https://github.com/LibreSprite/LibreSprite) 打开本目录的 `.aseprite` 文件即可编辑。`native-parts` 为实际像素，`native-materials` 为同名图层的材质遮罩。工程自带25帧和四段动作标签；头部使用关联帧，避免逐帧修改时错位。

各角色和替换部件位于不同图层。初始只显示麦穗的组合，其他图层可在编辑器中切换可见性。材质工程中的近黑颜色是编码，不是最终画面：R为材质编号，G为色阶，透明度为0或255。0保留原色，1肤色，2头发，3上衣，4围裙，7帽子，8虹膜。帽子当前保留原色。

不要移动画布或改变画布大小；新增、删除像素时，同步修改材质图的覆盖范围。编辑完运行 `python tools/classic_editor.py compile`，再验证动作和组合预览。完整说明见 [园丁管线](../../docs/GARDENER-PIPELINE.md)。

原始三角色及旧动作仍独立存档。本工程的隐藏部位、替换发型和脸型为项目素材的编辑衍生，不是从照片或 AI 服务生成的原画。来源及许可见 `release/THIRD-PARTY-NOTICES.md`。
