import os
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# 初始化 MCP 服务器实例
mcp = FastMCP("PrsAiPPT MCP Server", log_level="INFO")

# 用户API Key，这里对应接口中的 verification_code
VERIFICATION_CODE = os.getenv('VERIFICATION_CODE')
API_BASE = "https://www.prsai.cc"

def check_verification_code():
    """检查 VERIFICATION_CODE 是否已设置"""
    if not VERIFICATION_CODE:
        raise ValueError("VERIFICATION_CODE 环境变量未设置，请配置用户 API Key")
    return VERIFICATION_CODE

@mcp.tool()
async def check():
    """查询用户当前配置的 verification_code"""
    return os.getenv('VERIFICATION_CODE')

@mcp.tool()
async def translate_ppt(
    file_url: str = Field(description="需要翻译的PPT文件URL地址"),
    file_name: str = Field(description="PPT文件名，需包含.pptx或.ppt后缀"),
    target: str = Field(default="en", description="目标语言代码，如'en'表示英文"),
    query: str = Field(default="Translate PPT to English", description="翻译请求的描述或要求")
) -> dict:
    """
    Name:
        翻译PPT文件
    Description:
        调用PrsAi接口，将指定的PPT文件翻译为目标语言。
    Args:
        file_url: 需要翻译的PPT文件URL地址
        file_name: PPT文件名
        target: 目标语言代码
        query: 翻译请求描述
    Returns:
        翻译任务的结果，包含原始返回参数以及拼接的 output_url
    """
    check_verification_code()
    
    url = f"{API_BASE}/api/v1/ppt/translation_ppt"
    
    # 严格按照提供的 curl 命令设置 headers
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://www.prsai.cc',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.prsai.cc/',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
    }
    
    # 根据用户提供的 curl 命令，参数名为 filer_url
    payload = {
        "filer_url": file_url,
        "query": query,
        "verification_code": VERIFICATION_CODE,
        "file_name": file_name,
        "target": target
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
        res = response.json()
        
        # 提取 task_id (兼容直接在最外层或在 data 对象内)
        task_id = res.get('task_id')
        if not task_id and isinstance(res.get('data'), dict):
            task_id = res['data'].get('task_id')
            
        # 根据要求，mcp 返回的结果是原本 api 返回的参数，并在其中加入/修改 output_url
        if task_id:
            res['output_url'] = f"https://www.prsai.cc/?task_id={task_id}"
        else:
            # 容错处理
            res['output_url'] = "https://www.prsai.cc/?task_id="
            
        return res
        
    except httpx.HTTPStatusError as e:
        # 针对 HTTP 错误状态码提供更详细的错误信息
        raise Exception(f"API请求失败: HTTP {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        # 针对网络连接等请求错误
        raise Exception(f"网络请求失败: {str(e)}") from e
    except ValueError as e:
        raise Exception(str(e)) from e
    except Exception as e:
        raise Exception(f"PPT翻译请求失败: {str(e)}") from e
