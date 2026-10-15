import hashlib,json,os,sqlite3,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
ROOT=Path(__file__).resolve().parents[1]

class ConcurrentHarvestTests(unittest.TestCase):
 def test_two_processes_harvest_only_once_without_source_writes(self):
  with tempfile.TemporaryDirectory(prefix='garden-harvest-race-') as temp:
   home=Path(temp)/'codex';home.mkdir();data=Path(temp)/'collection'
   log=home/'rollout.jsonl';log.write_text(json.dumps({'type':'event_msg','payload':{'type':'task_complete','turn_id':'turn-one'}})+'\n')
   database=home/'state_5.sqlite'
   with closing(sqlite3.connect(database)) as conn:
    conn.execute('CREATE TABLE threads (id TEXT,title TEXT,cwd TEXT,updated_at INTEGER,rollout_path TEXT)')
    conn.execute('INSERT INTO threads VALUES (?,?,?,?,?)',('thread-one','test','test',int(time.time()),str(log)));conn.commit()
   digest=hashlib.sha256(database.read_bytes()).hexdigest()
   env={**os.environ,'CODEX_HOME':str(home),'CODEX_GARDEN_DATA':str(data)}
   processes=[subprocess.Popen([sys.executable,str(ROOT/'backend/bridge.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env) for _ in range(2)]
   request=json.dumps({'id':1,'method':'harvest','threadId':'thread-one','plantKind':0})+'\n'
   with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda p:json.loads(p.communicate(request,timeout=15)[0]),processes))
   self.assertEqual(sum('result' in r for r in responses),1,responses)
   self.assertEqual(json.loads((data/'harvest.json').read_text())['threads']['thread-one']['count'],1)
   self.assertEqual(hashlib.sha256(database.read_bytes()).hexdigest(),digest)
