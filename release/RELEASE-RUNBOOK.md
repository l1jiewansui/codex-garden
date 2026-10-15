# 发布操作手册

发布者为 risu1。当前版本 0.10.0-rc.2，目标平台 Windows x64。候选包可本地验证，公共发布必须通过全部门槛。

## 可重复构建

使用 Node >=22.12、Python 3.13.12、PyInstaller 6.22.3 与 hooks-contrib 2026.8。MCP 依赖固定在 mcp-requirements.lock。可用 .work/mcp-deps 做测试导入目录，实际发布构建使用独立 .work/build-venv，避免打入主环境的无关模块。构建不需要访问 Codex 账号或登录凭据。

```powershell
npm ci
python -m pip install -r release/mcp-requirements.lock --target .work/mcp-deps
python -m venv .work/build-venv
.work/build-venv/Scripts/python -m pip install -r release/mcp-requirements.lock pyinstaller==6.22.3 pyinstaller-hooks-contrib==2026.8
python -m unittest discover -s tests -v
node tests/world.test.cjs
node tests/desktop.test.cjs
node tests/update.test.cjs
.work/build-venv/Scripts/python -m PyInstaller --noconfirm --clean --onefile --console --name garden-bridge --distpath runtime --workpath .work/bridge-build --specpath .work --paths backend backend/bridge.py
.work/build-venv/Scripts/python -m PyInstaller --noconfirm --clean --onefile --console --name garden-mcp --distpath runtime --workpath .work/mcp-build --specpath .work --paths backend --copy-metadata mcp backend/mcp_server.py
python tools/release_metadata.py
python tools/package.py
python tools/prepare_listing_assets.py
python tools/validate_plugin.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/test_install.ps1 -PackagePath "$PWD/dist/desktop-pet-0.10.0-rc.2"
python tools/archive_release.py
python tools/build_plugin.py
```

验证 MCP 时将 .work/mcp-deps 加入 PYTHONPATH，运行 tools/test_mcp.py。验证桌面时运行 dist/desktop-pet-0.10.0-rc.2/CodexGarden.exe --qa；首次说明单独加 --qa-welcome。QA 写入包内 resources/app/verification，发布归档前重新打包。

完整插件内同时包含桌面程序与本地 MCP；不使用 lifecycle hooks。stdio 服务只暴露三个无参数工具。不得加入任意命令、任意路径读取、代收获或改写 Codex 的工具。

工作区根目录 .agents/plugins/marketplace.json 已登记此本地候选包，策略为 AVAILABLE。本机已通过 codex plugin marketplace add E:\gamekr 与 codex plugin add qingyun-garden@risu1-local-plugins --json 安装启用。CLI 查询已确认 installed=true、enabled=true；桌面插件界面与新对话调用仍需单独验收，不重启正在使用的宿主。

## 公共提交门槛

填写 PUBLISHER.json 的真实 HTTPS 官网、支持、隐私和服务条款地址，并部署对应页面。完成 OpenAI 发布组织身份验证以及本地 MCP approved-partner 资格。取得可信代码签名证书和签名工具，签名后重建哈希与归档。不要用自签名冒充可信签名。

运行 tools/release_gate.py 会生成 verification/public-release-gate.json；有失败项时不得称作已上架版本。官网页面是待部署稿，不代表已有可访问 URL。签名脚本不包含私钥或口令。

## 回滚与支持

不自动联网更新。保留上一版完整包，更新异常时从托盘退出当前版再启动上一版；不可降级到不支持当前收藏格式的旧版本。卸载默认保留收藏与设置，禁止在安装升级中清理用户数据。排障先导出收藏，并提醒备份包含对话标识。反馈仅请求版本、系统缩放、复现步骤和裁剪截图，不索取凭据或完整对话日志。

## 尚需外部验证

除本机自动化外，还需要在干净 Windows 电脑、多显示器/跨屏拖拽、不同显卡和长时休眠恢复场景验证。单机通过不等同于这些测试已经完成。
