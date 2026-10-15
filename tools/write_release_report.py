import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from release_paths import VERSION
gate=json.loads((ROOT/'verification/public-release-gate.json').read_text(encoding='utf-8'))
artifacts=json.loads((ROOT/f'verification/artifacts-{VERSION}.json').read_text())
rows='\n'.join(f"| {a['file']} | {a['bytes']/1024/1024:.1f} MiB | `{a['sha256']}` |" for a in artifacts['archives'])
blocked='\n'.join('- '+c['check']+'：'+c['detail'] for c in gate['checks'] if not c['passed'])
body=f'''# codex-garden · 上架前交付记录

版本 **{VERSION}**，发布者 **risu1**。可用的本地发布候选包已完成，本机 Codex CLI 已安装并启用插件；尚未在公共目录上架。

## 已完成

- 桌面程序、便携包、当前用户安装/卸载脚本、SHA256 清单及完整归档校验。
- 独立插件封装：便携清单、本地 stdio MCP、使用技能、商店图标与演示截图。无需用户另装 Node/Python。
- 三个无参数工具：打开菜园、查看状态数量、查看植物收藏。首次确认前不读数据；工具不返回对话标题、正文、路径和标识。
- 36 项 Python 测试、3 组 Node 测试；真实两进程收获去重、原始数据库未改写、损坏恢复与未来格式保护。
- 打包程序在 100%、125%、150%、200% 强制设备缩放下完成交互回归，包含收获、跳转、穿透蒙版、人物照料、收藏与面板。分数缩放原生外框允许最多2 DIP取整；避免尺寸反馈累积，卡片位置以组件为基准验证。此测试不替代真实多显示器实测。
- 打包程序首次使用确认测试、真实安装/开始菜单/注册/卸载测试，设置保留。
- 原生 Electron 单实例升级交接测试，使用隔离入口和实际升级策略。未冒充完整生产入口的升级端到端测试。
- 125% 下完整交互后持续运行180秒，18次状态与资源采样通过；仅为短时稳定性证据。
- npm 审计及30项固定 MCP 依赖审计未报告已知漏洞，不代表不存在未知问题。
- 已安装 Codex 缓存中的 MCP 握手与三个工具定义实测，全部缓存文件哈希校验通过。
- 隐私说明、使用条款页面稿、产品/帮助页面稿、商店文案、第三方许可及依赖清单、签名脚本和发布门槛检查脚本。

## 可交付文件

| 文件（dist 目录） | 大小 | SHA256 |
|---|---:|---|
{rows}

日常启动可用工作区“启动菜园.cmd”。本地插件名 qingyun-garden@risu1-local-plugins；现有聊天工具列表可能需要宿主刷新或新对话才可见，未擅自重启当前工作中的 Codex。

## 仍未满足的公共发布条件

{blocked}

外部资料空值保留在 release/PUBLISHER.json，没有伪造邮箱、网站、发布资格或证书。官网稿在 release/site，当前没有对外部署。官方本地 MCP 发布资格要求见 https://developers.openai.com/plugins/deploy/submission 。签名准备完成不等于已获得可信签名。

## 复核入口

完整构建步骤见 RELEASE-RUNBOOK.md，审核用例见 REVIEW-TEST-CASES.md。机器可读证据均在 verification。公开发布门槛为 public-release-gate.json，当前 publicReleaseReady=false；待真实资料与外部验收补齐后重跑，不能直接改成通过。
'''
(ROOT/'release/PRELAUNCH-STATUS.md').write_text(body,encoding='utf-8');print(ROOT/'release/PRELAUNCH-STATUS.md')
