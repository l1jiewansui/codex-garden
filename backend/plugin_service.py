"""Restricted local plugin facade. Never returns conversation identifiers or text."""
import json, os, subprocess, sys
from pathlib import Path

PLANTS=('胡萝卜','卷心菜','番茄','南瓜','玉米','茄子','草莓','向日葵','月光花','水晶菇','星灯草','黄金萝卜','月玉卷心菜','星露番茄','琥珀南瓜','豌豆炮手','双荚炮手','火炬辣椒','铃铛蘑菇','捕虫花','星月莲')

def consented():
    root=Path(os.environ.get('APPDATA',str(Path.home()/'AppData/Roaming')))
    try:return json.loads((root/'codex-garden-pet-v06/welcome.json').read_text(encoding='utf-8')).get('accepted') is True
    except (OSError,ValueError,AttributeError):return False

def application():
    # Frozen server lives at <plugin>/server/garden-mcp.exe. No user-supplied executable path.
    root=Path(sys.executable).resolve().parent.parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]/'plugin'
    return root/'app/CodexGarden.exe'

def launch():
    executable=application()
    if not executable.is_file():return {'ok':False,'message':'本地应用不完整，请重新安装菜园插件。'}
    subprocess.Popen([str(executable)],cwd=str(executable.parent),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    return {'ok':True,'message':'已请求打开桌面菜园；首次使用请点击“开始种菜”。'}

def status():
    if not consented():return {'connection':'welcome','message':'请先打开桌面菜园并完成首次使用说明。'}
    import bridge
    try:
        snap=bridge.snapshot();counts={}
        for thread in snap['threads']:
            key=thread.get('status','unknown');counts[key]=counts.get(key,0)+1
        return {'connection':snap['connection'],'counts':counts,'visibleLimit':24,'message':snap.get('error')}
    except Exception:return {'connection':'unavailable','message':'暂时无法读取本地菜园，请在桌面查看连接状态。'}

def collection():
    if not consented():return {'connection':'welcome','message':'请先打开桌面菜园并完成首次使用说明。'}
    import bridge
    try:
        inventory=bridge.inventory_of(bridge.load_state())
        return {'plants':[{'name':PLANTS[int(k)],'count':v} for k,v in inventory.items() if v>0],'total':sum(inventory.values())}
    except Exception:return {'connection':'unavailable','message':'收藏暂时无法读取，原文件和备份已保留。'}
