"""Versioned collection storage; atomic writes and validated rotating backups."""
import json,os,tempfile,time,shutil
from pathlib import Path
from contextlib import contextmanager

class StorageError(ValueError):pass

def validate(raw):
    if not isinstance(raw,dict):raise StorageError('收藏格式不正确')
    if 'schemaVersion' in raw:
        if raw['schemaVersion']!=1:raise StorageError('收藏来自较新版本，请先更新菜园')
        raw=raw.get('threads')
    if not isinstance(raw,dict):raise StorageError('收藏格式不正确')
    for key,record in raw.items():
        if not isinstance(key,str) or not isinstance(record,dict):raise StorageError('收藏条目不正确')
        count=record.get('count',0)
        if type(count) is not int or count<0:raise StorageError('收藏数量不正确')
        if record.get('turn') is not None and not isinstance(record['turn'],str):raise StorageError('收藏轮次不正确')
        items=record.get('items',{})
        if not isinstance(items,dict):raise StorageError('收藏品种不正确')
        for kind,n in items.items():
            if not isinstance(kind,str) or not kind.isdigit() or not 0<=int(kind)<15 or type(n) is not int or n<0:raise StorageError('收藏品种不正确')
        if sum(items.values())>count:raise StorageError('收藏总数不一致')
    return raw

def read(path):return validate(json.loads(Path(path).read_text(encoding='utf-8')))

def load(folder):
    folder=Path(folder);primary=folder/'harvest.json'
    candidates=[primary,folder/'harvest.recovery.json']+[folder/f'harvest.bak.{i}.json' for i in range(1,4)]
    existing=False
    for index,path in enumerate(candidates):
        if not path.exists():continue
        existing=True
        try:return read(path),('收藏已从备份恢复' if index else None)
        except StorageError as exc:
            # Never roll back a valid but newer schema to an older backup.
            if '较新版本' in str(exc):raise
        except (OSError,ValueError,UnicodeError):pass
    if existing:raise StorageError('收藏暂时无法读取，原文件已保留，请从托盘打开收藏文件夹查看备份')
    return {},None

def atomic_write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='harvest-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def save(folder,state):
    state=validate(state);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    primary=folder/'harvest.json'
    if primary.exists():
        try:previous=read(primary)
        except StorageError as exc:
            if '较新版本' in str(exc):raise
            previous=None
        except (OSError,ValueError,UnicodeError):previous=None
        if previous is None:
            shutil.copy2(primary,folder/f'harvest.damaged-{time.time_ns()}.json')
        else:
            for index in (3,2):
                source=folder/f'harvest.bak.{index-1}.json'
                if source.exists():os.replace(source,folder/f'harvest.bak.{index}.json')
            atomic_write(folder/'harvest.bak.1.json',{'schemaVersion':1,'threads':previous})
    atomic_write(primary,{'schemaVersion':1,'threads':state})
    try:atomic_write(folder/'harvest.recovery.json',{'schemaVersion':1,'threads':state})
    except OSError:return False
    return True

@contextmanager
def storage_lock(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    with (folder/'collection.lock').open('a+b') as stream:
        stream.seek(0,2)
        if stream.tell()==0:stream.write(b'0');stream.flush()
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            for attempt in range(40):
                try:msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError:
                    if attempt==39:raise StorageError('收藏正在保存，请稍后重试')
                    time.sleep(.05)
            try:yield
            finally:stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(stream,fcntl.LOCK_UN)
