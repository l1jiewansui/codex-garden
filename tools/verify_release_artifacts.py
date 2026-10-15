"""Verify final archives and the actual Codex plugin cache without launching UI."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def verify_folder(folder):
    manifest=json.loads((folder/'SHA256.json').read_text(encoding='utf-8'))
    for relative,digest in manifest.items():
        path=(folder/relative).resolve()
        assert path.is_relative_to(folder.resolve()) and path.is_file(),relative
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,relative
    return len(manifest)

archives=[]
for name in ('QingyunGarden-0.10.0-rc.1-Windows.zip','qingyun-garden-plugin-0.10.0-rc.1.zip'):
    file=ROOT/'dist'/name;digest=hashlib.sha256(file.read_bytes()).hexdigest()
    assert file.with_suffix('.zip.sha256').read_text().split()[0]==digest
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in archive.namelist())
    archives.append({'file':name,'sha256':digest,'bytes':file.stat().st_size})
folder=Path.home()/'.codex/plugins/cache/risu1-local-plugins/qingyun-garden/0.10.0-rc.1'
records=json.loads((ROOT/'verification/rc010-host-plugin-list.json').read_text(encoding='utf-8-sig'))['installed']
assert len(records)==1 and records[0]['installed'] and records[0]['enabled']
assert json.loads((ROOT/'verification/rc010-mcp-qa.json').read_text())['passed']
host={'passed':True,'pluginId':records[0]['pluginId'],'version':'0.10.0-rc.1','installed':True,'enabled':True,'cacheVerifiedFiles':verify_folder(folder),'cacheMcpProtocolTest':True,'uiAndNewChatValidation':False}
(ROOT/'verification/rc010-host-install.json').write_text(json.dumps(host,indent=2),encoding='utf-8')
report={'passed':True,'archives':archives,'desktopVerifiedFiles':verify_folder(ROOT/'dist/desktop-pet-rc010'),'pluginVerifiedFiles':verify_folder(ROOT/'dist/qingyun-garden-plugin-0.10.0-rc.1')}
(ROOT/'verification/rc010-artifacts.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
