import unittest,importlib.util,json,tempfile
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('attention_bridge',Path(__file__).resolve().parents[1]/'backend/bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class AttentionTests(unittest.TestCase):
 def test_completion_does_not_imply_unread(self):
  self.assertEqual(b.attention_for('a',[set()]),'read')
  self.assertEqual(b.attention_for('a',[{'a'}]),'unread')
  self.assertEqual(b.attention_for('a',None),'unknown')
 def test_conflicting_identities_are_not_guessed(self):
  self.assertEqual(b.attention_for('a',[{'a'},set()]),'unknown')
  self.assertEqual(b.attention_for('a',[{'a'},{'a'}]),'unread')
 def test_only_local_records_are_used(self):
  with tempfile.TemporaryDirectory() as folder,patch.object(b,'HOME',Path(folder)):
   p=Path(folder)/'.codex-global-state.json'
   p.write_text(json.dumps({'electron-thread-read-state-v1':{'version':1,'unreadByIdentity':{'account':{'local:one':['a'],'durable:cloud':['b']}}}}))
   self.assertEqual(b.read_attention(),[{'a'}])
   p.write_text('{');self.assertIsNone(b.read_attention())
