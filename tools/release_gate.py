"""Fail closed for public publication; local RC packaging remains possible."""
import hashlib,json,subprocess,sys,urllib.request,urllib.parse,os
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
from release_paths import VERSION,APP
publisher=json.loads((ROOT/'release/PUBLISHER.json').read_text(encoding='utf-8'))
checks=[]
shell_environment=dict(os.environ)
for key in list(shell_environment):
    if key.lower()=='psmodulepath':shell_environment.pop(key)
def check(name,passed,reason):checks.append({'check':name,'passed':bool(passed),'detail':reason})
for field in ('websiteURL','supportURL','privacyPolicyURL','termsOfServiceURL'):
    value=publisher.get(field)
    valid=False;detail='必须提供并部署真实 HTTPS 页面；当前未填写'
    if isinstance(value,str):
        url=urllib.parse.urlsplit(value)
        if url.scheme=='https' and url.hostname and not url.username and not url.password and 'example.' not in url.hostname:
            try:
                with urllib.request.urlopen(value,timeout=10) as response:valid=response.status==200;detail=f'{value}: HTTP {response.status}'
            except Exception:detail='页面暂时无法公开访问：'+value
    check(field,valid,detail)
for field in ('verifiedOrganization','localMcpApprovedPartner'):
    check(field,publisher.get(field) is True,'需要实际发布组织验证与本地 MCP 发布资格，不能由构建脚本授予')
app=APP
for relative in ('CodexGarden.exe','resources/app/runtime/garden-bridge.exe'):
    exe=app/relative
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',"(Get-AuthenticodeSignature -LiteralPath '"+str(exe).replace("'","''")+"').Status.ToString()"],capture_output=True,text=True,env=shell_environment)
    status=result.stdout.strip();check('signature:'+relative,status=='Valid',status or '未能验证可信签名')
result=subprocess.run(['powershell.exe','-NoProfile','-Command',"(Get-AuthenticodeSignature -LiteralPath '"+str(ROOT/'runtime/garden-mcp.exe').replace("'","''")+"').Status.ToString()"],capture_output=True,text=True,env=shell_environment)
check('signature:garden-mcp.exe',result.stdout.strip()=='Valid',result.stdout.strip() or '未能验证可信签名')
manifest=json.loads((app/'SHA256.json').read_text(encoding='utf-8'));actual={str(p.relative_to(app)) for p in app.rglob('*') if p.is_file() and p.name!='SHA256.json'}
integrity=set(manifest)==actual
for name,digest in manifest.items():
    path=(app/name).resolve()
    integrity=integrity and path.is_relative_to(app.resolve()) and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest
check('packageIntegrity',integrity,f'{len(manifest)} files; exact manifest match required')
audit=json.loads((ROOT/'verification/rc010-npm-audit.json').read_text(encoding='utf-8-sig'))
check('npmAudit',audit.get('metadata',{}).get('vulnerabilities',{}).get('total')==0,'当前依赖审计')
audit=json.loads((ROOT/'verification/rc010-python-audit.json').read_text(encoding='utf-8'))
check('pythonAudit',all(not d.get('vulns') for d in audit.get('dependencies',[])) and len(audit.get('dependencies',[]))==30,'固定的30项 MCP 依赖审计')
for name in ('rc5-dpi-1-garden-qa','rc5-welcome-qa','install-'+VERSION+'-lifecycle','mcp-'+VERSION+'-qa','rc5-final-garden-qa','rc5-dpi-2-garden-qa'):
    path=ROOT/f'verification/{name}.json'
    check(name,path.is_file() and json.loads(path.read_text(encoding='utf-8-sig')).get('passed') is True,'本轮实际自动化报告')
check('externalWindowsValidation',False,'待干净 Windows、多显示器、休眠恢复与长时间试用实测')
host=ROOT/f'verification/host-install-{VERSION}.json'
check('hostCLIInstallValidation',host.is_file() and json.loads(host.read_text(encoding='utf-8')).get('passed') is True,'Codex CLI 安装、启用与缓存内 MCP 实测')
check('hostPluginUIValidation',False,'CLI 已安装启用；桌面插件界面与新对话调用尚未验收')
report={'version':VERSION,'checkedAt':datetime.now(timezone.utc).isoformat(),'publicReleaseReady':all(c['passed'] for c in checks),'checks':checks}
(ROOT/'verification/public-release-gate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True,indent=2))
sys.exit(0 if report['publicReleaseReady'] else 2)
