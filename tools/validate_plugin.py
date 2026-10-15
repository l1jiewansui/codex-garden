import json,sys
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]
folder=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'plugin'
for name in ('plugin','mcp'):
    schema=json.loads((ROOT/f'release/schemas/{name}.schema.json').read_text())
    data=json.loads((folder/f'{name}.json').read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator(schema).validate(data)
manifest=json.loads((folder/'plugin.json').read_text(encoding='utf-8'))
assert manifest['version']==json.loads((ROOT/'package.json').read_text(encoding='utf-8'))['version']
assert manifest['author']['name']=='risu1'
assert manifest['extensions']['com.openai']['requires_local_executor'] is True
interface=manifest['extensions']['com.openai']['interface']
for field,limit in (('displayName',30),('shortDescription',30),('longDescription',4000),('developerName',80)):
    assert 0<len(interface[field])<=limit,field
for field in ('logo','composerIcon'):
    asset=(folder/interface[field]).resolve()
    assert asset.is_relative_to(folder.resolve()) and asset.is_file(),field
for relative in interface.get('screenshots',[]):
    asset=(folder/relative).resolve();assert asset.is_relative_to(folder.resolve()) and asset.is_file()
assert not any(folder.glob('**/hooks.json')),'Public submissions cannot contain lifecycle hooks'
assert (folder/'skills/desktop-garden/SKILL.md').is_file()
print('Official plugin/MCP schemas and local semantic checks passed.')
