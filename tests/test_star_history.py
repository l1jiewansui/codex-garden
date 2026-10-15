import unittest
from xml.etree import ElementTree
from tools.update_star_history import record_snapshot,render

class StarHistoryTests(unittest.TestCase):
 def test_daily_dedup_and_decreases_are_real(self):
  data=record_snapshot({},'owner/repo',4,'2026-10-15')
  data=record_snapshot(data,'owner/repo',6,'2026-10-15')
  data=record_snapshot(data,'owner/repo',3,'2026-10-16')
  self.assertEqual(data['snapshots'],[{'date':'2026-10-15','stars':6},{'date':'2026-10-16','stars':3}])
  ElementTree.fromstring(render(data))
 def test_first_snapshot_does_not_invent_history(self):
  data=record_snapshot({},'owner/repo',0,'2026-10-15');svg=render(data)
  self.assertEqual(len(data['snapshots']),1);self.assertNotIn('<polyline',svg);self.assertIn('First snapshot',svg)
  ElementTree.fromstring(svg)
 def test_wrong_repo_and_invalid_values_are_rejected(self):
  with self.assertRaises(ValueError):record_snapshot({'repository':'other/repo'},'owner/repo',1,'2026-10-15')
  for count in (-1,True,'5'):
   with self.assertRaises(ValueError):record_snapshot({},'owner/repo',count,'2026-10-15')
 def test_themes_embed_outlines_and_are_deterministic(self):
  data=record_snapshot({},'owner/repo',0,'2026-10-15')
  light=render(data);dark=render(data,'dark')
  self.assertEqual(light,render(data))
  self.assertIn('#ffffff',light);self.assertIn('#0d1117',dark)
  self.assertNotIn('@font-face',light);self.assertNotIn('<script',light)
  self.assertIn('role="img"',light);ElementTree.fromstring(dark)
