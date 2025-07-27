import platform
import time
import sys
import psutil
from fastapi import APIRouter,Depends
from typing import Dict, Any
from core.auth import get_current_user
from .base import success_response, error_response
from driver.token import wx_cfg
from core.config import cfg
from jobs.mps import TaskQueue
from driver.success import WX_LOGIN_ED,WX_LOGIN_INFO
router = APIRouter(prefix="/sys", tags=["系统信息"])

# 记录服务器启动时间
_START_TIME = time.time()
@router.get("/base_info", summary="常规信息")
async def get_base_info() -> Dict[str, Any]:
    try:
        from .ver import API_VERSION
        from core.ver import VERSION as CORE_VERSION,LATEST_VERSION
        base_info = {
            'api_version': API_VERSION,
            'core_version': CORE_VERSION,
            "ui":{
                "name": cfg.get("server.name",""),
                "web_name": cfg.get("server.web_name","WeRss公众号订阅平台"),
            }
        }
        return success_response(data=base_info)
    except Exception as e:
        return error_response(
            code=50001,
            message=f"获取信息失败: {str(e)}"
        )    
    

 # 缓存不会频繁变动的系统信息
_STATIC_INFO = {
    'cpu': {
        'cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count(logical=True)
    },
    'memory': {
        'total': round(psutil.virtual_memory().total / (1024 ** 3), 2)
    },
    'disk': {
        'total': round(psutil.disk_usage('./').total / (1024 ** 3), 2)
    }
}
@router.get("/resources", summary="获取系统资源使用情况")
async def get_system_resources(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取系统资源使用情况
    
    Returns:
        BaseResponse格式的资源使用信息，包括:
        - cpu: CPU使用率(%)
        - memory: 内存使用情况
        - disk: 磁盘使用情况
    """
   

    try:
        # 获取动态变化的资源信息
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('./')
        # 单位转换函数
        def to_gb(bytes_value):
            return round(bytes_value / (1024 ** 3), 2)
        
        resources_info = {
            'cpu': {
                'percent': cpu_percent,
                'cores': _STATIC_INFO['cpu']['cores'],
                'threads': _STATIC_INFO['cpu']['threads']
            },
            'memory': {
                'total': _STATIC_INFO['memory']['total'],
                'used': to_gb(mem.used),
                'free': to_gb(mem.free),
                'percent': mem.percent
            },
            'disk': {
                'total': _STATIC_INFO['disk']['total'],
                'used': to_gb(disk.used),
                'free': to_gb(disk.free),
                'percent': disk.percent
            }
        }
        return success_response(data=resources_info)
    except Exception as e:
        return error_response(
            code=50002,
            message=f"获取系统资源失败: {str(e)}"
        )

@router.get("/info", summary="获取系统信息")
async def get_system_info(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前系统的各种信息
    
    Returns:
        BaseResponse格式的系统信息，包括:
        - os: 操作系统信息
        - python_version: Python版本
        - uptime: 服务器运行时间(秒)
        - system: 系统详细信息
    """
    try:
        from core.article_lax import ARTICLE_INFO,laxArticle
        from .ver import API_VERSION
        from core.ver import VERSION as CORE_VERSION,LATEST_VERSION

        # 获取系统信息
        system_info = {
            'os': {
                'name': platform.system(),
                'version': platform.version(),
                'release': platform.release(),
            },
            'python_version': sys.version,
            'uptime': round(time.time() - _START_TIME, 2),
            'system': {
                'node': platform.node(),
                'machine': platform.machine(),
                'processor': platform.processor(),
            },
            'api_version': API_VERSION,
            'core_version': CORE_VERSION,
            'latest_version':LATEST_VERSION,
            'need_update':CORE_VERSION != LATEST_VERSION,
            "wx":{
                'token':wx_cfg.get('token',''),
                'expiry_time':wx_cfg.get('expiry.expiry_time','') if WX_LOGIN_ED else "-",
                "info":WX_LOGIN_INFO,
                "login":WX_LOGIN_ED,
            },
            "article":laxArticle(),
            'queue':TaskQueue.get_queue_info(),
        }
        return success_response(data=system_info)
    except Exception as e:
        return error_response(
            code=50001,
            message=f"获取系统信息失败: {str(e)}"
        )