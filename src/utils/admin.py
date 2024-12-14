import ctypes
import sys
import os
import logging
import traceback
from pathlib import Path

def is_admin():
    """检查是否具有管理员权限"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        logging.debug(f"当前管理员权限状态: {is_admin}")
        return is_admin
    except Exception as e:
        logging.error(f"检查管理员权限时出错: {str(e)}")
        return False

def run_as_admin():
    """以管理员权限重启程序"""
    try:
        import ctypes, sys, os
        from pathlib import Path
        
        # 获取当前脚本的完整路径
        script_path = Path(sys.argv[0]).resolve()
        work_dir = script_path.parent
        
        # 构建新的命令行参数
        if sys.argv[0].endswith('.py'):
            args = [
                sys.executable,
                str(script_path),
                '--admin',
                '--debug'  # 添加调试标记
            ]
        else:
            args = [str(script_path), '--admin', '--debug']
        
        # 记录启动信息
        log_dir = Path.home() / '.env_manager' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / 'admin_restart.log', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"尝试管理员权限重启\n")
            f.write(f"工作目录: {work_dir}\n")
            f.write(f"完整命令: {' '.join(args)}\n")
        
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            args[0],
            ' '.join(args[1:]),
            str(work_dir),
            1
        )
        
        with open(log_dir / 'admin_restart.log', 'a', encoding='utf-8') as f:
            f.write(f"ShellExecuteW 返回值: {ret}\n")
        
        return ret > 32
        
    except Exception as e:
        # 记录错误信息
        log_dir = Path.home() / '.env_manager' / 'logs'
        with open(log_dir / 'admin_restart.log', 'a', encoding='utf-8') as f:
            f.write(f"权限提升错误: {str(e)}\n")
        return False

def ensure_admin():
    """确保程序以管理员权限运行"""
    if not is_admin():
        logging.info("正在请求管理员权限...")
        return run_as_admin()
    logging.info("已经具有管理员权限")
    return True
