"""Native Electron single-instance/relaunch smoke test, using isolated fixture apps."""
import json,os,shutil,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def wait_for(test,seconds=20):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if test():return
        time.sleep(.2)
    raise AssertionError('Native upgrade test timed out')

def run():
    # Preserve scratch evidence; no deletion of user applications or settings.
    scratch=Path(tempfile.mkdtemp(prefix='garden-native-upgrade-',dir=ROOT/'.work'));events=scratch/'events.jsonl'
    script="""const {app}=require('electron'),fs=require('node:fs');
const path=require('node:path'),version=require('./package.json').version,{upgradeExecutable}=require('./update-policy.cjs');
app.setPath('userData',process.env.GARDEN_UPGRADE_PROFILE);
function log(event){fs.appendFileSync(process.env.GARDEN_UPGRADE_EVENTS,JSON.stringify({event,version})+'\\n');}
if(!app.requestSingleInstanceLock({version,executable:process.execPath})){app.quit();}
else{app.whenReady().then(()=>{log('ready');if(version==='0.10.0-rc.1')setTimeout(()=>app.quit(),500);});
app.on('second-instance',(_e,_a,_c,data)=>{const executable=upgradeExecutable(data,version);if(executable){log('handoff');app.relaunch({execPath:executable,args:[]});app.quit();}});}
setTimeout(()=>app.quit(),25000);
"""
    paths=[]
    for version in ('0.10.0-beta.1','0.10.0-rc.1'):
        target=scratch/version
        shutil.copytree(ROOT/'node_modules/electron/dist',target,copy_function=os.link)
        (target/'electron.exe').rename(target/'CodexGarden.exe')
        app=target/'resources/app';app.mkdir()
        (app/'main.cjs').write_text(script,encoding='utf-8')
        (app/'package.json').write_text(json.dumps({'name':'codex-garden','version':version,'main':'main.cjs'}))
        shutil.copy2(ROOT/'update-policy.cjs',app/'update-policy.cjs');paths.append(target/'CodexGarden.exe')
    env={**os.environ,'GARDEN_UPGRADE_PROFILE':str(scratch/'profile'),'GARDEN_UPGRADE_EVENTS':str(events)}
    old=subprocess.Popen([str(paths[0])],env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    wait_for(lambda:events.exists() and 'ready' in events.read_text())
    candidate=subprocess.Popen([str(paths[1])],env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));candidate.wait(timeout=20)
    wait_for(lambda:sum('ready' in line for line in events.read_text().splitlines())==2)
    old.wait(timeout=20);records=[json.loads(line) for line in events.read_text().splitlines()]
    assert [(r['event'],r['version']) for r in records]==[('ready','0.10.0-beta.1'),('handoff','0.10.0-beta.1'),('ready','0.10.0-rc.1')],records
    report={'passed':True,'scope':'Native Electron lifecycle with real upgrade-policy, isolated fixture entrypoint; not full production main','events':records,'scratch':str(scratch)}
    (ROOT/'verification/rc010-native-upgrade.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':run()
