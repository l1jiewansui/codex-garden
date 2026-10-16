import importlib.util,json,tempfile,unittest,sqlite3,time,os,hashlib
from unittest.mock import patch
from contextlib import closing
from pathlib import Path
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).resolve().parents[1]/'backend/bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def event(kind,**p):return json.dumps({'type':'event_msg','timestamp':'now','payload':{'type':kind,**p}})

class AdapterTests(unittest.TestCase):
    def test_thread_names_use_latest_rename_ignore_invalid_lines(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(b,'HOME',Path(folder)):
            self.assertEqual(b.thread_names(),{})
            records=[{'id':'one','thread_name':'旧标题'},{'id':'two','thread_name':'API (2)'},{'id':'one','thread_name':'新标题'},None,{'id':'two','thread_name':' ' }]
            (Path(folder)/'session_index.jsonl').write_text('\n'.join(json.dumps(r) for r in records)+'\n{broken',encoding='utf-8')
            self.assertEqual(b.thread_names(),{'one':'新标题','two':'API (2)'})
    def test_pinned_order_precedes_stable_non_pinned_and_activity(self):
        rows=[{'id':str(i),'updated_at':100-i} for i in range(30)]
        result=b.order_rows(rows,['29','3','missing'])
        self.assertEqual([r['id'] for r in result[:4]],['29','3','0','1'])
        self.assertEqual(len(result),30)
        rows[0]['updated_at']=999999
        self.assertEqual(b.order_rows(rows,['29','3','missing']),result)

    def test_sidebar_local_order_ignores_remote_and_duplicates(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(b,'HOME',Path(folder)):
            path=Path(folder)/'.codex-global-state.json'
            path.write_text(json.dumps({'electron-persisted-atom-state':{'unified-sidebar-pinned-order-v1':['codex:thread:local:b','codex:thread:remote:x','chatgpt:conversation:y','codex:thread:local:a','codex:thread:local:b']}}))
            self.assertEqual(b.sidebar_order(),['b','a'])
            path.write_text('{')
            self.assertEqual(b.sidebar_order(),[])
    def test_next_turn_resets_old_completion(self):
        s=b.parse_events([event('task_started',turn_id='one'),event('task_complete',turn_id='one',last_agent_message='done'),event('task_started',turn_id='two')])
        self.assertEqual((s['status'],s['turn'],s['summary']),('growing','two',''))
    def test_unknown_and_incomplete_json(self):
        self.assertEqual(b.parse_events(['{','{}'])['status'],'unknown')
    def test_interruption_does_not_ripen(self):
        self.assertEqual(b.parse_events([event('task_started',turn_id='a'),event('turn_aborted')])['status'],'paused')
    def test_harvest_once_and_new_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            oldhome,olddata=b.HOME,b.DATA;b.HOME=Path(tmp);b.DATA=Path(tmp)/'garden'
            try:
                log=Path(tmp)/'rollout.jsonl';log.write_text(event('task_started',turn_id='one')+'\n'+event('task_complete',turn_id='one')+'\n')
                db=Path(tmp)/'state_5.sqlite'
                with closing(sqlite3.connect(db)) as c:
                    c.execute('CREATE TABLE threads (id TEXT,title TEXT,cwd TEXT,updated_at INTEGER,rollout_path TEXT,archived INTEGER,has_user_event INTEGER,source TEXT)')
                    c.execute('INSERT INTO threads VALUES (?,?,?,?,?,0,0,?)',('t','title','project',int(time.time()),str(log),'vscode'));c.commit()
                self.assertEqual(b.snapshot()['threads'][0]['status'],'ripe')
                (Path(tmp)/'session_index.jsonl').write_text(json.dumps({'id':'t','thread_name':'修改后的标题'}),encoding='utf-8')
                self.assertEqual(b.snapshot()['threads'][0]['title'],'修改后的标题')
                original=hashlib.sha256(db.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):b.handle({'method':'harvest','threadId':'t','plantKind':99})
                self.assertEqual(b.snapshot()['inventory'],{})
                b.handle({'method':'harvest','threadId':'t','plantKind':9})
                self.assertEqual(sum(b.snapshot()['inventory'].values()),1)
                self.assertEqual(b.snapshot()['threads'][0]['status'],'harvested')
                with self.assertRaises(ValueError): b.handle({'method':'harvest','threadId':'t'})
                with log.open('a') as f:f.write(event('task_started',turn_id='two')+'\n'+event('task_complete',turn_id='two')+'\n')
                self.assertEqual(b.snapshot()['threads'][0]['status'],'ripe')
                b.handle({'method':'harvest','threadId':'t'})
                self.assertEqual(b.snapshot()['harvestCount'],2)
                self.assertEqual(sum(b.snapshot()['inventory'].values()),2)
                self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(),original)
            finally:b.HOME,b.DATA=oldhome,olddata
    @unittest.skipUnless(os.name=='nt','Windows long path')
    def test_windows_extended_prefix(self):
        self.assertEqual(b.canonical('\\\\?\\'+str(b.HOME)),b.canonical(b.HOME))
    def test_cached_running_state_becomes_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            oldhome=b.HOME;b.HOME=Path(tmp)
            try:
                p=Path(tmp)/'rollout.jsonl';p.write_text(event('task_started',turn_id='a'))
                self.assertEqual(b.inspect_log(str(p))['status'],'growing')
                with patch.object(b.time,'time',return_value=time.time()+1000):
                    self.assertEqual(b.inspect_log(str(p))['status'],'stale')
            finally:b.HOME=oldhome
    def test_path_outside_codex_rejected(self):
        self.assertEqual(b.inspect_log(str(Path(__file__).resolve()))['status'],'unknown')
    def test_latest_database_schema_is_checked(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(b,'HOME',Path(folder)),patch.object(b,'DATA',Path(folder)/'data'):
            db=Path(folder)/'state_8.sqlite'
            with closing(sqlite3.connect(db)) as c:c.execute('CREATE TABLE threads (id TEXT)');c.commit()
            self.assertEqual(b.find_database(),db)
            self.assertEqual(b.snapshot()['connection'],'incompatible')
    def test_missing_database_preserves_collection(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(b,'HOME',Path(folder)),patch.object(b,'DATA',Path(folder)/'data'):
            b.save_state({'t':{'turn':'one','count':2,'items':{'9':2}}})
            result=b.snapshot();self.assertEqual(result['connection'],'missing');self.assertEqual(result['inventory'],{'9':2})

if __name__=='__main__':unittest.main()
