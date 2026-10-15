"""stdio only; no listening ports, credentials, arbitrary paths or write tools."""
import asyncio,sys,anyio
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool,ToolAnnotations
import plugin_service

server=Server('qingyun-garden',version='0.10.0-rc.1')
FUNCTIONS={'garden_launch':plugin_service.launch,'garden_status':plugin_service.status,'garden_collection':plugin_service.collection}
DESCRIPTIONS={'garden_launch':'用户要求时打开本地桌面菜园；首次使用须在应用内确认。','garden_status':'只读取菜园状态数量，不返回对话标题、标识或正文。','garden_collection':'只读取已收获植物的品种与数量，不执行收获。'}

@server.list_tools()
async def list_tools():
    return [Tool(name=name,description=DESCRIPTIONS[name],inputSchema={'type':'object','properties':{},'additionalProperties':False},annotations=ToolAnnotations(readOnlyHint=name!='garden_launch',destructiveHint=False,idempotentHint=True,openWorldHint=False)) for name in FUNCTIONS]

@server.call_tool()
async def call_tool(name,arguments):
    if name not in FUNCTIONS or arguments:raise ValueError('不支持此工具或参数')
    return FUNCTIONS[name]()

async def main():
    # Reuse standard streams so temporary TextIOWrappers cannot close their buffers at shutdown.
    sys.stdin.reconfigure(encoding='utf-8',errors='replace');sys.stdout.reconfigure(encoding='utf-8')
    async with stdio_server(anyio.wrap_file(sys.stdin),anyio.wrap_file(sys.stdout)) as (read,write):
        await server.run(read,write,server.create_initialization_options())

if __name__=='__main__':asyncio.run(main())
