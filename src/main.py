#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统环境管理工具
用于管理Windows系统环境变量和系统工具的集成工具
"""

import os
import sys
import time
import ctypes
import logging
from pathlib import Path
from datetime import datetime
import tkinter.messagebox as messagebox

# 基础路径设置
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

class Application:
    def __init__(self):
        self.app_data_dir = Path.home() / '.env_manager'
        self.logger = None
        self.config = None
        self.window = None
        
        # 确保基本目录存在
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
    def initialize(self):
        """初始化应用程序"""
        try:
            # 1. 初始化日志系统
            if not self._init_logging():
                return False
                
            # 2. 检查运行环境
            if not self._check_environment():
                return False
                
            # 3. 检查管理员权限
            if not self._check_admin():
                return False
                
            # 4. 加载配置
            if not self._init_config():
                return False
                
            self.logger.info("应用程序初始化完成")
            return True
            
        except Exception as e:
            self._handle_error("初始化失败", e)
            return False
            
    def _init_logging(self):
        """初始化日志系统"""
        try:
            from src.utils.logger import LogManager
            if not LogManager().init_logging(self.app_data_dir / 'logs'):
                raise RuntimeError("日志系统初始化失败")
            self.logger = logging.getLogger('EnvManager')
            return True
        except Exception as e:
            messagebox.showerror("错误", f"日志系统初始化失败:\n{str(e)}")
            return False
            
    def _check_environment(self):
        """检查运行环境"""
        try:
            if not sys.platform.startswith('win'):
                raise RuntimeError("此程序只能在 Windows 系统上运行")
            if sys.version_info < (3, 7):
                raise RuntimeError("需要 Python 3.7 或更高版本")
            return True
        except Exception as e:
            self._handle_error("环��检查失败", e)
            return False
            
    def _check_admin(self):
        """检查管理员权限"""
        try:
            from src.utils.admin import is_admin, run_as_admin
            
            if not is_admin():
                self.logger.info("尝试获取管理员权限...")
                if run_as_admin():
                    self.logger.info("已成功以管理员权限重启程序")
                    sys.exit(0)
                else:
                    messagebox.showerror("错误", "请右键选择'以管理员身份运行'来启动程序")
                    return False
                    
            self.logger.info("已验证管理员权限")
            return True
            
        except Exception as e:
            self._handle_error("权限检查失败", e)
            return False
            
    def _init_config(self):
        """初始化配置"""
        try:
            from src.utils.config import Config
            self.config = Config()
            return True
        except Exception as e:
            self._handle_error("配置加载失败", e)
            return False
            
    def _handle_error(self, prefix: str, error: Exception):
        """统一错误处理"""
        error_msg = f"{prefix}: {str(error)}"
        if self.logger:
            self.logger.error(error_msg, exc_info=True)
        messagebox.showerror("错误", error_msg)
        
    def start_gui(self):
        """启动图形界面"""
        try:
            from src.gui.main_window import MainWindow
            self.window = MainWindow(self.config)
            if self.window:
                self.window.root.protocol("WM_DELETE_WINDOW", self.window.on_closing)
                self.window.root.mainloop()
                return True
            return False
        except Exception as e:
            self._handle_error("GUI启动失败", e)
            return False

def main():
    """程序入口"""
    # 检查是否是管理员权限重启
    is_admin_restart = "--admin" in sys.argv
    
    # 如果是管理员重启，等待旧进程退出
    if is_admin_restart:
        time.sleep(1)
    
    # 在非调试模式下隐藏控制台
    if sys.platform.startswith('win') and '--debug' not in sys.argv:
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    app = Application()
    if app.initialize():
        return 0 if app.start_gui() else 1
    return 1

if __name__ == "__main__":
    sys.exit(main())
