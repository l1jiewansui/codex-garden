# 独立动作制作记录

使用内置 ImageGen，以 `assets/pixel-v04/gardeners.png` 中四个人物为外观参考生成新图集，随后用现有固定版本 FrameRonin 转为共享 47 色、二值透明度像素图。

原图：`E:/gamekr/CodexGarden/assets/art-v09/independent-actions.png`。
运行图集：`E:/gamekr/CodexGarden/assets/pixel-v09/actions.png`。
像素处理与校验记录：`E:/gamekr/CodexGarden/assets/pixel-v09/manifest.json`。

最终提示词的核心约束：四位原人物保持可辨识外观；透明背景八列四行，每行一个人物；第1–2列空手待机、无工具，第3–5列独立浇水（举壶、倾倒、收回，恰好一个蓝色水壶），第6–8列独立施肥（举起棕色袋子、倾撒颗粒、收回，恰好一个袋子且没有水壶）；固定比例、足部锚点和单帧边界，原创 Terraria-inspired 侧视像素风。完整调用提示见本对话生成记录。

输出为1774×887原图。处理使用固定行脚底坐标与统一240像素画布，不逐帧改变身体大小；每帧降采样为44像素后置入48像素画布。运行时直接播放独立图帧，不再在旧持壶姿态上叠加道具。图集中含有绘制的水流/颗粒，运行粒子补充工具落点的动态反馈。
