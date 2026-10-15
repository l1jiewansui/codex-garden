"""Names shared by release builders; existing released versions remain untouched."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION=json.loads((ROOT/'package.json').read_text(encoding='utf-8'))['version']
APP=ROOT/'dist'/('desktop-pet-'+VERSION)
PLUGIN=ROOT/'dist'/('qingyun-garden-plugin-'+VERSION)
WINDOWS_ZIP=ROOT/'dist'/('codex-garden-'+VERSION+'-windows.zip')
PLUGIN_ZIP=ROOT/'dist'/('codex-garden-'+VERSION+'-plugin.zip')
