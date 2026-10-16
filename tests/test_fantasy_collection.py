import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from backend import bridge

class FantasyCollectionTests(unittest.TestCase):
 def test_new_plants_harvest_and_keep_hidden_ids_reserved(self):
  with tempfile.TemporaryDirectory() as folder,patch.object(bridge,'DATA',Path(folder)),patch.object(bridge,'secret_plant',return_value=None),patch.object(bridge,'snapshot',return_value={'threads':[{'id':'plant','turn':'one','crop':15,'status':'ripe'}]}):
   result=bridge.handle({'method':'harvest','threadId':'plant','plantKind':15})
   self.assertEqual(result['inventory'],{'15':1})
   for kind in (11,14,21,True):
    with self.assertRaises(ValueError):bridge.handle({'method':'harvest','threadId':'plant','plantKind':kind})
