"""Real stdio handshake/tools calls against the bundled MCP executable."""
import asyncio,json,os,sqlite3,sys,tempfile,time
from pathlib import Path
from contextlib import closing
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1]

async def test():
    with tempfile.TemporaryDirectory(prefix='garden-mcp-test-') as temp:
        folder=Path(temp);home=folder/'codex';home.mkdir();roaming=folder/'Roaming'
        executable=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'runtime/garden-mcp.exe'
        params=StdioServerParameters(command=str(executable),args=[],env={**os.environ,'APPDATA':str(roaming),'CODEX_HOME':str(home),'CODEX_GARDEN_DATA':str(folder/'collection')})
        async with stdio_client(params) as (read,write),ClientSession(read,write) as session:
            await session.initialize();tools=await session.list_tools()
            assert {t.name for t in tools.tools}=={'garden_launch','garden_status','garden_collection'}
            assert all(not t.inputSchema.get('properties') for t in tools.tools)
            for name in ('garden_status','garden_collection'):
                result=await session.call_tool(name,{})
                assert not result.isError,str(result)
                assert json.loads(result.content[0].text)['connection']=='welcome'
            assert not (folder/'collection').exists(),'Unexpected collection access before consent'
            welcome=roaming/'codex-garden-pet-v06/welcome.json';welcome.parent.mkdir(parents=True);welcome.write_text('{"accepted":true}',encoding='utf-8')
            result=await session.call_tool('garden_status',{});assert json.loads(result.content[0].text)['connection']=='missing'
            log=home/'rollout.jsonl';log.write_text(json.dumps({'type':'event_msg','payload':{'type':'task_complete','turn_id':'private-turn'}})+'\n')
            with closing(sqlite3.connect(home/'state_5.sqlite')) as conn:
                conn.execute('CREATE TABLE threads (id TEXT,title TEXT,cwd TEXT,updated_at INTEGER,rollout_path TEXT)')
                conn.execute('INSERT INTO threads VALUES (?,?,?,?,?)',('private-id','secret-title','secret-path',int(time.time()),str(log)))
                conn.commit()
            result=await session.call_tool('garden_status',{});text=result.content[0].text;data=json.loads(text)
            assert data['connection']=='ready' and data['counts']=={'ripe':1},text
            assert all(value not in text for value in ('private-id','secret-title','secret-path','private-turn'))
            data=json.loads((await session.call_tool('garden_collection',{})).content[0].text);assert data['total']==0
            rejected=await session.call_tool('garden_status',{'path':'C:/private'})
            assert rejected.isError,'Unknown input was not rejected'
        report={'passed':True,'protocol':'stdio MCP SDK initialize/list_tools/call_tool','tools':3,'consentGating':True,'aggregateOnly':True,'unknownArgumentsRejected':True}
        (ROOT/'verification/rc010-mcp-qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':asyncio.run(test())
