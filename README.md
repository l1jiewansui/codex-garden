# codex-garden

Windows 透明桌面伴侣，将本机 Codex 对话状态可视化为像素菜园。发布者 risu1，当前为 0.10.0-rc.1，已制作本地测试插件，尚未上架公共目录。

使用说明见 README-PET.md，隐私说明见 PRIVACY.md。

## 本地开发

需要 Windows x64、Node.js 22.12+ 和 Python 3.13。首次运行：

```powershell
python -m pip install -r requirements-dev.txt
npm ci
npm start
```

源代码模式可直接使用 Python 桥接程序，不需要先下载打包后的运行时。运行 `npm test` 检查核心逻辑和资源；桌面交互验证需在有 Codex 本地对话的 Windows 桌面会话中运行 `npm run qa`。

本仓库不提交本机对话、收藏、凭据、验证截图、依赖缓存或安装包。安装包单独作为 GitHub Release 附件分发。已处理的像素资源随源代码保存，可以直接运行；重新生成美术时，部分工具依赖同级的 XiuXianPixelStudio 工程及其固定 FrameRonin 管线，详见 ART-DIRECTION-V04.md。

开发需要 Node.js 22.12+、Python 3.10+，安装依赖后运行 npm start。npm test 检查状态解析、阅读状态、像素资源、收藏恢复和升级策略。npm run qa 验证桌面交互；electron . --qa --qa-welcome 单独验证首次使用前不读取对话。

桥接构建命令：python -m PyInstaller --onefile --paths backend --name garden-bridge --distpath runtime --workpath .work/bridge-beta010 --specpath .work backend/bridge.py

随后运行 python tools/package.py 输出发布目录，包含运行时、安装与卸载脚本、使用说明和 SHA256 清单。

安装器支持 -TestMode -NoLaunch：仅复制到系统临时目录，不创建快捷方式、注册表项或启动程序。测试模式不等同于真实 Windows 安装、升级及卸载验证。

Codex 本地数据库使用只读连接，并检查字段；阅读状态冲突时不猜测。收藏格式支持从旧版记录迁移到版本1，写入由进程锁与原子替换保护。拒绝不识别的未来版本，避免错误降级覆盖。

原始生图不进入发布包。资源来源和许可见各 assets/pixel-* 目录及 release/THIRD-PARTY-NOTICES.md。第三方清单、上架文案、官网和政策页面稿已准备；完整操作见 release/RELEASE-RUNBOOK.md。公开发布仍需真实政策/支持地址、发布身份与本地 MCP 资格、可信签名及外部 Windows 验证。verification/public-release-gate.json 是逐项检查结果，不用空值冒充已完成。
