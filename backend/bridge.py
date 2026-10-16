"""Read-only Codex adapter. No credentials, prompts or source DB writes."""
import sys, os, json, sqlite3, time, hashlib
from contextlib import closing
from pathlib import Path
try:
    from state_store import load as load_collection,save as save_collection,storage_lock
except ModuleNotFoundError:
    from backend.state_store import load as load_collection,save as save_collection,storage_lock

HOME = Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))
DATA = Path(os.environ.get('CODEX_GARDEN_DATA', str(Path.home()/'.codex-garden')))
LOG_CACHE = {}
STORAGE_NOTICE=None

def canonical(path):
    value=str(Path(path).resolve())
    if os.name=='nt':
        if value.startswith('\\\\?\\UNC\\'): value='\\\\'+value[8:]
        elif value.startswith('\\\\?\\'): value=value[4:]
    return Path(value)

def parse_events(lines):
    state = {'status':'unknown', 'turn':None, 'summary':'', 'plan':None}
    for line in lines:
        try: e=json.loads(line)
        except (ValueError, UnicodeError): continue
        p=e.get('payload', {}); kind=p.get('type'); typ=e.get('type')
        if typ=='event_msg':
            if kind in ('task_started','turn_started'):
                state={'status':'growing','turn':p.get('turn_id') or e.get('timestamp'), 'summary':'', 'plan':None}
            elif kind in ('task_complete','task_completed','turn_completed'):
                state['status']='ripe'; state['summary']=str(p.get('last_agent_message') or state['summary'])[:2400]
                state['turn']=p.get('turn_id') or state['turn'] or e.get('timestamp')
            elif kind in ('turn_aborted','task_interrupted'): state['status']='paused'
            elif kind in ('task_failed','error'): state['status']='failed'
        if typ=='response_item' and kind=='message' and p.get('role')=='assistant' and p.get('phase')=='final_answer':
            state['summary']='\n'.join(c.get('text','') for c in p.get('content',[]) if c.get('type')=='output_text')[:2400]
        # A tool call alone never proves the turn has completed or needs approval.
    return state

def inspect_log(path):
    p=Path(path)
    if not p.is_absolute() or not canonical(p).is_relative_to(canonical(HOME)): return {'status':'unknown','turn':None,'summary':'','plan':None}
    try:
        stat=p.stat(); stamp=(stat.st_size,stat.st_mtime_ns)
        if str(p) in LOG_CACHE and LOG_CACHE[str(p)][0]==stamp:
            result=dict(LOG_CACHE[str(p)][1])
            if result['status']=='growing' and time.time()-stat.st_mtime>900: result['status']='stale'
            return result
        with p.open('rb') as f:
            start=max(0,stat.st_size-4*1024*1024); f.seek(start)
            if start: f.readline()
            lines=f.read().decode('utf-8',errors='replace').splitlines()
        result=parse_events(lines)
        LOG_CACHE[str(p)]=(stamp,result)
        result=dict(result)
        if result['status']=='growing' and time.time()-stat.st_mtime>900: result['status']='stale'
        return dict(result)
    except OSError: return {'status':'unknown','turn':None,'summary':'','plan':None}

def load_state():
    global STORAGE_NOTICE
    state,STORAGE_NOTICE=load_collection(DATA)
    return state

def save_state(state):
    global STORAGE_NOTICE
    if not save_collection(DATA,state):STORAGE_NOTICE='收藏已保存，备份暂不可用'

def find_database():
    files=[]
    for path in HOME.glob('state_*.sqlite'):
        version=path.stem.removeprefix('state_')
        if version.isdigit():files.append((int(version),path))
    return max(files,key=lambda item:item[0])[1] if files else None

def read_attention():
    """Read only explicit local unread records; never infer read state from completion."""
    try:
        raw=json.loads((HOME/'.codex-global-state.json').read_text(encoding='utf-8'))
        state=raw.get('electron-thread-read-state-v1',{})
        if state.get('version')!=1:return None
        identities=state.get('unreadByIdentity',{})
        groups=[]
        for hosts in identities.values():
            if not isinstance(hosts,dict):continue
            local=[v for k,v in hosts.items() if k.startswith('local:') and isinstance(v,list)]
            if local:groups.append(set(x for values in local for x in values if isinstance(x,str)))
        return groups or None
    except (OSError,ValueError,AttributeError):return None

def attention_for(thread_id,groups):
    if not groups:return 'unknown'
    votes=[thread_id in group for group in groups]
    return 'unread' if all(votes) else 'read' if not any(votes) else 'unknown'

def sidebar_order():
    """Read local pinned order only; never persist into Codex state."""
    try:
        raw=json.loads((HOME/'.codex-global-state.json').read_text(encoding='utf-8'))
        atoms=raw.get('electron-persisted-atom-state',{})
        unified=atoms.get('unified-sidebar-pinned-order-v1')
        if isinstance(unified,list):
            return list(dict.fromkeys(v.removeprefix('codex:thread:local:') for v in unified if isinstance(v,str) and v.startswith('codex:thread:local:')))
        for values in (atoms.get('app-server-pinned-thread-order-v1'),raw.get('pinned-thread-ids')):
            if isinstance(values,list):return list(dict.fromkeys(v for v in values if isinstance(v,str)))
    except (OSError,ValueError,AttributeError):pass
    return []

def thread_names():
    """Session index contains the names explicitly assigned in the desktop app."""
    names={}
    try:
        with (HOME/'session_index.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                try:record=json.loads(line)
                except (ValueError,UnicodeError):continue
                if not isinstance(record,dict):continue
                identity,name=record.get('id'),record.get('thread_name')
                if isinstance(identity,str) and isinstance(name,str) and name.strip():
                    names[identity]=name.strip()
    except (OSError,UnicodeError):pass
    return names

def order_rows(rows,pinned):
    ranks={value:index for index,value in enumerate(pinned)}
    # Query provides stable creation order for non-pinned conversations.
    return sorted(rows,key=lambda row:ranks.get(row['id'],len(ranks)))[:24]

def inventory_of(state):
    result={}
    for record in state.values():
        for kind,count in record.get('items',{}).items():
            if kind.isdigit() and 0<=int(kind)<15 and isinstance(count,int) and count>0:result[kind]=result.get(kind,0)+count
    return result

def secret_plant(thread_id,turn):
    h=2166136261
    for c in thread_id+'|'+str(turn or 'initial'):h=((h^ord(c))*16777619)&0xffffffff
    return (h>>4)%4 if h%16==0 else None

def snapshot():
    harvested=load_state();attention=read_attention();names=thread_names()
    base={'inventory':inventory_of(harvested),'storageNotice':STORAGE_NOTICE,'harvestCount':sum(v.get('count',0) for v in harvested.values())}
    db=find_database()
    if db is None:return {**base,'threads':[], 'error':'还没有找到对话，请先打开 Codex。','connection':'missing'}
    with closing(sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=2)) as conn:
        conn.row_factory=sqlite3.Row
        columns={row[1] for row in conn.execute('PRAGMA table_info(threads)')}
        if not {'id','title','cwd','updated_at','rollout_path'}<=columns:return {**base,'threads':[],'error':'当前 Codex 版本暂不兼容，请更新菜园。','connection':'incompatible'}
        clauses=[]
        if 'archived' in columns:clauses.append('archived=0')
        if 'source' in columns:clauses.append("COALESCE(source,'') NOT LIKE '%subagent%'")
        where=' WHERE '+' AND '.join(clauses) if clauses else ''
        stable='created_at DESC,id ASC' if 'created_at' in columns else 'id DESC'
        rows=conn.execute('SELECT id,title,cwd,updated_at,rollout_path FROM threads'+where+' ORDER BY '+stable).fetchall()
        rows=order_rows(rows,sidebar_order())
    threads=[]
    for row in rows:
        d=dict(row); path=d.pop('rollout_path'); d.update(inspect_log(path))
        d['title']=names.get(d['id'],d['title']) or '未命名对话'
        # The desktop UI needs titles and state, not project paths or message excerpts.
        for field in ('cwd','summary','plan'):d.pop(field,None)
        d['crop']=int(hashlib.sha256(d['id'].encode()).hexdigest()[:8],16)%3
        d['attention']=attention_for(d['id'],attention)
        if d['status']=='ripe' and harvested.get(d['id'],{}).get('turn')==d['turn']: d['status']='harvested'
        threads.append(d)
    return {**base,'threads':threads,'error':None,'connection':'ready','scannedAt':time.time()}

def handle(req):
    if req.get('method')=='snapshot': return snapshot()
    if req.get('method')=='export':return {'schemaVersion':1,'threads':load_state()}
    if req.get('method')=='harvest':
        with storage_lock(DATA):return harvest_request(req)
    raise ValueError('未知请求')

def harvest_request(req):
        thread=next((t for t in snapshot()['threads'] if t['id']==req.get('threadId')),None)
        if not thread or thread['status']!='ripe': raise ValueError('这一茬尚未成熟，或已经收获。')
        kind=req.get('plantKind',thread['crop'])
        if not isinstance(kind,int) or isinstance(kind,bool) or not 0<=kind<15:raise ValueError('无效植物')
        secret=secret_plant(thread['id'],thread['turn'])
        if secret is not None:kind=11+secret
        elif kind>=11:raise ValueError('本轮不是隐藏款')
        s=load_state();prev=s.get(thread['id'],{});items=dict(prev.get('items',{}));items[str(kind)]=items.get(str(kind),0)+1
        s[thread['id']]={'turn':thread['turn'],'count':prev.get('count',0)+1,'at':time.time(),'items':items};save_state(s)
        return {'ok':True,'inventory':inventory_of(s)}

if __name__=='__main__':
    for line in sys.stdin:
        try:
            req=json.loads(line); result={'id':req.get('id'),'result':handle(req)}
        except Exception as exc: result={'id':locals().get('req',{}).get('id'),'error':str(exc)}
        print(json.dumps(result,ensure_ascii=True),flush=True)
