"""Offline product/policy site draft. Does not publish or invent URLs."""
import html,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'release/site';out.mkdir(exist_ok=True)
style='''body{margin:0;background:#25252f;color:#f6eac3;font:17px/1.8 system-ui,sans-serif}main{max-width:840px;margin:auto;padding:64px 24px}nav a{margin-right:24px}a{color:#bdd078}h1{font-size:42px;line-height:1.25}h2{color:#f5c86c}figure{background:#36343a;padding:24px;border:2px solid #706c55;margin:32px 0}img{max-width:100%;image-rendering:pixelated}footer{margin-top:64px;color:#c3ba8b;border-top:2px solid #706c55;padding-top:20px}.tag{color:#bdd078}'''
def page(file,title,body):
    (out/file).write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · 青云桌面菜园</title><style>{style}</style><main><nav><a href="index.html">菜园</a><a href="privacy.html">隐私</a><a href="terms.html">使用条款</a><a href="support.html">帮助</a></nav>{body}<footer>青云桌面菜园 · risu1</footer></main></html>',encoding='utf-8')
page('index.html','让对话长成一片菜园','''<p class="tag">Windows · 二维像素桌面伙伴</p><h1>让对话长成<br>桌面上的一片菜园。</h1><p>一颗种子，一轮工作。让生长、成熟和微光，陪你看见对话的变化。</p><figure><img src="garden.png" alt="演示菜园：像素园丁、蔬菜、太阳和收藏箱"><figcaption>示例画面，不含真实对话。</figcaption></figure><h2>轻轻照料，继续专注</h2><p>点击走近，双击收获并回到对话。给植物浇水、施肥，收藏特殊品种；这些互动不会改变真实工作进度。</p><h2>留在本机，融入桌面</h2><p>透明区域支持鼠标穿透，不抢键盘输入。拖动太阳就能移动菜园。首次确认后才读取本机 Codex 数据，无广告与遥测。</p><p>成熟代表观察到一轮完成，不等于任务验收通过。需要 Windows x64 与 Codex 桌面版。</p>''')
privacy=(ROOT/'PRIVACY.md').read_text(encoding='utf-8')
page('privacy.html','隐私说明',''.join('<h1>'+html.escape(p[2:])+'</h1>' if p.startswith('# ') else '<p>'+html.escape(p)+'</p>' for p in privacy.split('\n\n')))
page('terms.html','使用条款','''<h1>使用条款</h1><p>发布者：risu1。你可以在本人拥有或获授权的 Windows 设备上安装并使用青云桌面菜园。第三方组件遵循安装包中附带的各自许可。</p><p>菜园根据本机 Codex 记录呈现状态，可能受到记录延迟或格式变化影响。请在原始对话中确认任务结果，不将植物成熟作为执行成功或验收通过的凭证。</p><p>浇水、施肥和隐藏植物是装饰互动，不会给 Codex 增加执行能力。菜园不修改 Codex 数据库，也不自动同步阅读状态。</p><p>收藏在本机保存。卸载默认保留收藏与设置；建议升级前通过托盘菜单导出备份。不要公开含对话标识的备份文件。</p><p>当前为候选测试版本，可能存在缺陷与兼容性限制。安装使用前请阅读隐私说明和随包文档。</p>''')
page('support.html','使用帮助','''<h1>使用帮助</h1><h2>开始种菜</h2><p>运行菜园，阅读首次说明并点击“开始种菜”。没有对话时先打开 Codex，等待几秒。只显示最近24个未归档对话。</p><h2>找不到窗口</h2><p>右键系统托盘的菜园图标，选择“显示桌面菜园”或“移回屏幕右下角”。双击托盘图标可以恢复鼠标交互。</p><h2>移动与收获</h2><p>拖动太阳移动组件，单击菜地让园丁走近，双击植物打开对话。成熟植物同时收入收藏箱。浇水和施肥只有动画效果。</p><h2>收藏与问题反馈</h2><p>通过托盘导出收藏备份。遇到问题时记录应用版本、Windows 版本、缩放比例和复现步骤；截图请遮住对话名称，不提供登录凭据或完整对话日志。</p><p>公开支持联系方式尚未配置。本帮助页为待发布稿，正式上线前会补齐支持入口。</p>''')
source=ROOT/'verification/garden-v091.png'
if source.is_file():shutil.copy2(source,out/'garden.png')
print(out)
