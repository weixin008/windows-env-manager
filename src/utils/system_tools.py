import os
import json
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional, List
from src.utils.resource import resource_path

# 获取系统目录
SYSTEM_ROOT = os.environ.get('SystemRoot', 'C:\\Windows')
SYSTEM32 = Path(SYSTEM_ROOT) / 'System32'

# 系统工具路径映射
TOOLS_PATH = {
    # 系统管理
    'msinfo32.exe': 'msinfo32',
    'msconfig.exe': 'msconfig',
    'taskmgr.exe': 'taskmgr',
    'services.msc': 'services.msc',
    'eventvwr.msc': 'eventvwr.msc',
    'compmgmt.msc': 'compmgmt.msc',
    'perfmon.exe': 'perfmon',
    'resmon.exe': 'resmon',
    
    # 系统配置
    'sysdm.cpl': 'sysdm.cpl',
    'certmgr.msc': 'certmgr.msc',
    'gpedit.msc': 'gpedit.msc',
    'netplwiz': 'netplwiz',
    'timedate.cpl': 'timedate.cpl',
    'intl.cpl': 'intl.cpl',
    'powercfg.cpl': 'powercfg.cpl',
    'rundll32.exe': 'rundll32',
    
    # 硬件管理
    'devmgmt.msc': 'devmgmt.msc',
    'diskmgmt.msc': 'diskmgmt.msc',
    'printmanagement.msc': 'printmanagement.msc',
    'mmsys.cpl': 'mmsys.cpl',
    'desk.cpl': 'desk.cpl',
    'control printers': 'control printers',
    
    # 网络工具
    'ncpa.cpl': 'ncpa.cpl',
    'mstsc.exe': 'mstsc',
    'firewall.cpl': 'firewall.cpl',
    'wf.msc': 'wf.msc',
    'ipconfig': 'ipconfig',
    'netsh': 'netsh',
    'fsmgmt.msc': 'fsmgmt.msc',
    
    # 安全工具
    'wscui.cpl': 'wscui.cpl',
    'secpol.msc': 'secpol.msc',
    
    # 命令行工具
    'cmd': 'cmd',
    'powershell': str(SYSTEM32 / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'),
    'control printers': 'control printers',
    'regedit.exe': 'regedit'
}

def run_system_tool(command: str, args: Optional[List[str]] = None) -> bool:
    """运行系统工具"""
    try:
        # 处理命令行工具
        if command == 'cmd':
            subprocess.Popen('cmd', creationflags=subprocess.CREATE_NEW_CONSOLE)
            return True
            
        if command == 'powershell':
            powershell_path = str(SYSTEM32 / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe')
            subprocess.Popen(
                [powershell_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True
            
        # 处理复合命令（如rundll32 sysdm.cpl,EditEnvironmentVariables）
        if ' ' in command:
            command_parts = command.split(' ')
            tool_name = TOOLS_PATH.get(command_parts[0], command_parts[0])
            process = subprocess.Popen([tool_name] + command_parts[1:])
            return True
            
        tool_name = TOOLS_PATH.get(command, command)
        
        # 特殊处理网络命令
        if command in ['ipconfig', 'netsh']:
            process = subprocess.Popen(
                [tool_name] + (args or []),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True
            
        # MMC工具处理
        elif command.endswith('.msc'):
            process = subprocess.Popen(['mmc', tool_name])
            return True
            
        # 控制面板项处理
        elif command.endswith('.cpl'):
            process = subprocess.Popen(['control', tool_name])
            return True
            
        # 其他工具处理
        else:
            process = subprocess.Popen([tool_name] + (args or []))
            return True
            
    except Exception as e:
        logging.error(f"运行工具出错: {str(e)}")
        return False

def load_tools_config():
    """加载工具配置"""
    try:
        config_path = resource_path('data/tools_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载工具配置失败: {str(e)}")
        return {}