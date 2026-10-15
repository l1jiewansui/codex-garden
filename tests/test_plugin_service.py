import sys,tempfile,json,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import plugin_service as service

class PluginTests(unittest.TestCase):
    def test_no_reads_before_consent(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',{'APPDATA':folder}),patch.dict(sys.modules,{'bridge':None}):
            self.assertEqual(service.status()['connection'],'welcome')
            self.assertEqual(service.collection()['connection'],'welcome')

    def test_only_aggregate_leaves_facade(self):
        from types import SimpleNamespace
        fake=SimpleNamespace(snapshot=lambda:{'connection':'ready','threads':[{'id':'private-id','title':'secret','status':'ripe'}]},load_state=lambda:{},inventory_of=lambda _: {'0':2})
        with patch.object(service,'consented',return_value=True),patch.dict(sys.modules,{'bridge':fake}):
            result=service.status();self.assertEqual(result['counts'],{'ripe':1})
            self.assertNotIn('private',json.dumps(result));self.assertNotIn('secret',json.dumps(result))
            self.assertEqual(service.collection()['total'],2)

    def test_errors_do_not_disclose_paths(self):
        from types import SimpleNamespace
        def fail():raise OSError('C:/private/user/conversation.json')
        with patch.object(service,'consented',return_value=True),patch.dict(sys.modules,{'bridge':SimpleNamespace(snapshot=fail)}):
            result=service.status();self.assertEqual(result['connection'],'unavailable');self.assertNotIn('private',str(result))

    def test_launch_has_no_user_controlled_command(self):
        with tempfile.TemporaryDirectory() as folder:
            executable=Path(folder)/'CodexGarden.exe';executable.touch()
            with patch.object(service,'application',return_value=executable),patch.object(service.subprocess,'Popen') as start:
                self.assertTrue(service.launch()['ok'])
                self.assertEqual(start.call_args.args[0],[str(executable)])
                self.assertNotIn('shell',start.call_args.kwargs)
