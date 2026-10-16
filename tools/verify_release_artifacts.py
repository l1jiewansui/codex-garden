"""Verify final archives and the actual Codex plugin cache without launching UI."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from release_paths import VERSION,APP,PLUGIN,WINDOWS_ZIP,PLUGIN_ZIP

def verify_folder(folder):
    manifest=json.loads((folder/'SHA256.json').read_text(encoding='utf-8'))
    for relative,digest in manifest.items():
        path=(folder/relative).resolve()
        assert path.is_relative_to(folder.resolve()) and path.is_file(),relative
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,relative
    return len(manifest)

archives=[]
for name in (WINDOWS_ZIP.name,PLUGIN_ZIP.name):
    file=ROOT/'dist'/name;digest=hashlib.sha256(file.read_bytes()).hexdigest()
    assert file.with_suffix('.zip.sha256').read_text().split()[0]==digest
    with zipfile.ZipFile(file) as archive:
        assert archive.testzip() is None
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in archive.namelist())
    archives.append({'file':name,'sha256':digest,'bytes':file.stat().st_size})
folder=Path.home()/'.codex/plugins/cache/risu1-local-plugins/qingyun-garden'/VERSION
records=json.loads((ROOT/f'verification/host-plugin-list-{VERSION}.json').read_text(encoding='utf-8-sig'))['installed']
records=[r for r in records if r.get('pluginId')=='qingyun-garden@risu1-local-plugins']
assert len(records)==1 and records[0]['installed'] and records[0]['enabled'] and records[0]['version']==VERSION
assert json.loads((ROOT/f'verification/mcp-{VERSION}-qa.json').read_text())['passed']
host={'passed':True,'pluginId':records[0]['pluginId'],'version':VERSION,'installed':True,'enabled':True,'cacheVerifiedFiles':verify_folder(folder),'cacheMcpProtocolTest':True,'uiAndNewChatValidation':False}
(ROOT/f'verification/host-install-{VERSION}.json').write_text(json.dumps(host,indent=2),encoding='utf-8')
report={'passed':True,'archives':archives,'desktopVerifiedFiles':verify_folder(APP),'pluginVerifiedFiles':verify_folder(PLUGIN)}
(ROOT/f'verification/artifacts-{VERSION}.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
