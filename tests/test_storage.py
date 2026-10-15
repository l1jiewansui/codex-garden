import json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
from backend import state_store as store

def state(n):return {'thread':{'turn':str(n),'count':n,'items':{'0':n}}}

class StorageTests(unittest.TestCase):
 def test_recovery_mirror_failure_keeps_committed_primary(self):
  with tempfile.TemporaryDirectory() as folder:
   original=store.atomic_write
   def write(path,value):
    if Path(path).name=='harvest.recovery.json':raise OSError('disk full')
    return original(path,value)
   with patch.object(store,'atomic_write',side_effect=write):self.assertFalse(store.save(folder,state(1)))
   self.assertEqual(store.load(folder),(state(1),None))
 def test_legacy_migration_and_rotation(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'harvest.json').write_text(json.dumps(state(1)))
   self.assertEqual(store.load(root)[0],state(1))
   for n in range(2,7):store.save(root,state(n))
   self.assertEqual(json.loads((root/'harvest.json').read_text())['schemaVersion'],1)
   self.assertEqual(store.read(root/'harvest.bak.1.json'),state(5))
   self.assertEqual(store.read(root/'harvest.bak.3.json'),state(3))
 def test_recover_latest_and_preserve_damage(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);store.save(root,state(1));store.save(root,state(2))
   (root/'harvest.json').write_text('{bad')
   recovered,notice=store.load(root);self.assertEqual(recovered,state(2));self.assertTrue(notice)
   store.save(root,state(3));self.assertEqual(store.load(root),(state(3),None))
   self.assertEqual(len(list(root.glob('harvest.damaged-*.json'))),1)
 def test_unrecoverable_is_not_reset(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'harvest.json').write_text('{bad')
   with self.assertRaises(store.StorageError):store.load(root)
   self.assertEqual((root/'harvest.json').read_text(),'{bad')
 def test_new_schema_is_not_rolled_back(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);store.save(root,state(1));(root/'harvest.json').write_text(json.dumps({'schemaVersion':2,'threads':state(2)}))
   with self.assertRaises(store.StorageError):store.load(root)
   with self.assertRaises(store.StorageError):store.save(root,state(3))
 def test_invalid_counts_are_rejected_before_writing(self):
  with tempfile.TemporaryDirectory() as folder:
   with self.assertRaises(store.StorageError):store.save(folder,{'t':{'count':0,'items':{'0':1}}})
   self.assertFalse((Path(folder)/'harvest.json').exists())
