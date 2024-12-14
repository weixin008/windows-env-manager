import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Callable
import json
from pathlib import Path
from ..utils.config import Config
from ..gui.widgets import ToolTip
from ..utils.system_tools import run_system_tool
import traceback
from PIL import Image, ImageTk
import os
from src.utils.resource import IMAGES_DIR, resource_path

class ToolsPanel(ttk.Frame):
    def __init__(self, parent: ttk.Frame, config: Config, run_callback: Callable):
        """初始化工具面板"""
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.run_callback = run_callback
        self.logger = logging.getLogger('ToolsPanel')
        
        # 加载工具配置
        self.tools_categories = self.load_tools_config()
        
        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建工具面板界面"""
        try:
            # 创建主框架
            main_frame = ttk.Frame(self)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 创建工具标签页
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 为每个分类创建标签页
            for category, info in self.tools_categories.items():
                frame = ttk.Frame(self.notebook, padding=5)
                frame.grid_columnconfigure(0, weight=1)
                
                # 添加描述标签
                ttk.Label(
                    frame, 
                    text=info["description"],
                    style="Title.TLabel",
                    wraplength=300
                ).grid(row=0, column=0, sticky='w', pady=(0, 10))
                
                # 创建工具按钮容器
                tools_frame = ttk.Frame(frame)
                tools_frame.grid(row=1, column=0, sticky='nsew')
                tools_frame.grid_columnconfigure((0,1), weight=1)
                
                # 添加工具按钮，每行两个
                for i, tool in enumerate(info["tools"]):
                    row = i // 2
                    col = i % 2
                    btn = ttk.Button(
                        tools_frame,
                        text=tool["name"],
                        style="Tool.TButton",
                        command=lambda c=tool["command"], n=tool["name"]: self.run_tool(n, c)
                    )
                    btn.grid(row=row, column=col, padx=5, pady=3, sticky='ew')
                    
                    if "tooltip" in tool:
                        ToolTip(btn, tool["tooltip"])
                
                self.notebook.add(frame, text=category)
            
            # 添加作者信息区域
            self._create_author_info(main_frame)
            
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def _create_author_info(self, parent):
        """创建使用说明区域"""
        try:
            # 创建一个带标题"使用说明"的LabelFrame容器
            help_frame = ttk.LabelFrame(parent, text="使用说明")
            help_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
            
            # 创建一个用于放置内容的Frame容器
            content_frame = ttk.Frame(help_frame)
            content_frame.pack(padx=20, pady=15)
            
            # 定义说明文本
            help_text = """系统环境管理工具 - 便捷管理系统环境变量和系统工具

【环境变量管理】
• 帮助您快速查看、修改和恢复系统环境变量
• 解决因误删或覆盖环境变量导致软件无法运行的问题
• 提供常用环境变量的一键添加功能

【系统工具集成】
• 集成了Windows系统常用管理工具的快捷入口
• 分类整理，方便查找和使用
• 支持工具说明提示

软件由公众号豆子爱分享开发，欢迎关注获取更多实用工具"""
            
            # 创建文本Label，左对齐
            ttk.Label(content_frame, text=help_text, justify="left").pack(side=tk.LEFT, padx=(0, 25))
            
            # 创建右侧按钮和图片框架
            right_frame = ttk.Frame(content_frame)
            right_frame.pack(side=tk.LEFT, padx=(25, 0))
            
            # 添加赞赏按钮
            ttk.Button(right_frame, text="赞赏作者", command=self._show_donate_code).pack(pady=(0, 10))
            
            # 加载并显示公众号二维码
            gzh_img = Image.open(IMAGES_DIR / "gzh.png")
            gzh_height = 90  # 设置高度
            aspect_ratio = gzh_img.width / gzh_img.height
            gzh_width = int(gzh_height * aspect_ratio)
            gzh_img = gzh_img.resize((gzh_width, gzh_height), Image.Resampling.LANCZOS)
            self.gzh_photo = ImageTk.PhotoImage(gzh_img)
            ttk.Label(right_frame, image=self.gzh_photo).pack()
            
        except Exception as e:
            self.logger.error(f"创建使用说明区域失败: {str(e)}")

    def _show_donate_code(self):
        """显示赞赏码"""
        try:
            # 创建新窗口
            donate_window = tk.Toplevel(self)
            donate_window.title("赞赏作者")
            
            # 设置窗口大小和位置
            window_width = 300
            window_height = 400
            screen_width = donate_window.winfo_screenwidth()
            screen_height = donate_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            donate_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # 加载赞赏码
            zsm_img = Image.open(IMAGES_DIR / "zsm.png")
            zsm_size = (250, 250)
            zsm_img.thumbnail(zsm_size, Image.Resampling.LANCZOS)
            self.zsm_photo = ImageTk.PhotoImage(zsm_img)
            
            # 显示赞赏码
            ttk.Label(donate_window, text="感谢您的支持！", font=('微软雅黑', 12)).pack(pady=10)
            ttk.Label(donate_window, image=self.zsm_photo).pack(pady=10)
            ttk.Button(donate_window, text="关闭", command=donate_window.destroy).pack(pady=10)
            
            # 使窗口置顶
            donate_window.transient(self)
            donate_window.grab_set()
            
        except Exception as e:
            self.logger.error(f"显示赞赏码失败: {str(e)}")

    def run_tool(self, name: str, command: str):
        """运行工具并记录日志"""
        try:
            self.logger.info(f"正在启动工具: {name}")
            success = run_system_tool(command)
            if success:
                self.run_callback(name, command)
        except Exception as e:
            self.logger.error(f"启动工具 {name} 失败: {str(e)}")

    def load_tools_config(self) -> Dict:
        """加载工具配置"""
        try:
            config_path = resource_path('data/tools_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
            
        except Exception as e:
            self.logger.error(f"加载工具配置失败: {str(e)}")
            return self.get_default_tools()

    def get_default_tools(self) -> Dict:
        """获取默认工具配置"""
        return {
            "硬件管理": {
                "description": "硬件相关具",
                "tools": [
                    {
                        "name": "打印机管理",
                        "command": "control printers",
                        "tooltip": "管理打印机"
                    },
                    {
                        "name": "系统信息",
                        "command": "msinfo32",
                        "tooltip": "查看系统详细信息"
                    },
                    {
                        "name": "系统配置",
                        "command": "msconfig",
                        "tooltip": "配置系统启动项"
                    },
                    {
                        "name": "任务管理器",
                        "command": "taskmgr",
                        "tooltip": "管理系统进程和性能"
                    },
                    {
                        "name": "服务管理",
                        "command": "services.msc",
                        "tooltip": "管理系统服务"
                    },
                    {
                        "name": "事件查看器",
                        "command": "eventvwr.msc",
                        "tooltip": "查看系统日志"
                    }
                ]
            },
            "系统配置": {
                "description": "系统设置相关工具",
                "tools": [
                    {
                        "name": "环境变量",
                        "command": "rundll32 sysdm.cpl,EditEnvironmentVariables",
                        "tooltip": "系统环境变量设"
                    },
                    {
                        "name": "注册表编辑器",
                        "command": "regedit",
                        "tooltip": "编辑系统注册表"
                    },
                    {
                        "name": "组策略辑器",
                        "command": "gpedit.msc",
                        "tooltip": "编辑本地组策略"
                    },
                    {
                        "name": "证书管理器",
                        "command": "certmgr.msc",
                        "tooltip": "管理系统证书"
                    }
                ]
            },
            "网络工具": {
                "description": "网络管理相关工具",
                "tools": [
                    {
                        "name": "网络连接",
                        "command": "ncpa.cpl",
                        "tooltip": "管理网络连接"
                    },
                    {
                        "name": "防火墙设置",
                        "command": "firewall.cpl",
                        "tooltip": "配置Windows防火墙"
                    },
                    {
                        "name": "高级防火墙",
                        "command": "wf.msc",
                        "tooltip": "高级防火墙配置"
                    },
                    {
                        "name": "远程桌面",
                        "command": "mstsc",
                        "tooltip": "远程连接其他计算机"
                    }
                ]
            }
        }
