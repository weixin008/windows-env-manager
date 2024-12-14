import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import os
from typing import Optional, Dict, List
import subprocess
import traceback
from pathlib import Path
from PIL import Image, ImageTk

from src.utils.config import Config
from src.utils.logger import LogManager
from src.utils.admin import is_admin, run_as_admin
from src.gui.tools_panel import ToolsPanel
from src.gui.env_panel import EnvPanel
from src.utils.system_tools import run_system_tool
from src.gui.settings_dialog import SettingsDialog
from src.gui.theme import UNIFIED_THEME, WIDGET_STYLES
from src.utils.resource import IMAGES_DIR, resource_path
from src.gui.widgets import ToolTip

from src.utils.resource import resource_path  # 添加这行导入

class MainWindow:
    _instance = None
    
    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(MainWindow, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
        
    def __init__(self, config: Config):
        """初始化主窗口"""
        # 防止重复初始化
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        # 初始化基本属性
        self.config = config
        self.logger = logging.getLogger('MainWindow')
        self.max_recent = 10
        self.recent_tools = []
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("系统环境管理工具")
        
        # 设置窗口属性
        self.setup_window()
        
        # 应用统一主题
        self.apply_theme()
        
        # 创建界面
        self.create_gui()
        
        self.initialized = True

    def setup_window(self):
        """配置窗口属性"""
        try:
            # 修改图标路径获取方式
            icon_path = resource_path('src/icon.png')
            if Path(icon_path).exists():
                icon_image = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon_image)
            
            # 设置窗口大小和位置
            window_width = 800
            window_height = 600
            
            # 获取屏幕尺寸
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # 计算窗口位置
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # 设置窗口大小和位置
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # 设置最小窗口大小
            self.root.minsize(600, 400)
            
            # 配置网格权重
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_rowconfigure(1, weight=1)
            
        except Exception as e:
            self.logger.error(f"设置窗口属性失败: {str(e)}")

    def create_gui(self):
        """创建主界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 最近使用下拉框
        self.recent_combo = ttk.Combobox(
            toolbar, 
            width=20,
            state='readonly'
        )
        self.recent_combo.pack(side=tk.LEFT, padx=5)
        self.recent_combo.set('最近使用')
        self.recent_combo.bind('<<ComboboxSelected>>', self.on_recent_selected)
        
        
        # 字体大小下拉框
        self.font_var = tk.StringVar(value="9")
        font_label = ttk.Label(toolbar, text="字体:")
        font_label.pack(side=tk.RIGHT, padx=(5,0))
        font_menu = ttk.OptionMenu(
            toolbar,
            self.font_var,
            "9",
            "8", "9", "10", "11", "12",
            command=self.apply_font
        )
        font_menu.pack(side=tk.RIGHT, padx=5)
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工具面板
        self.tools_panel = ToolsPanel(
            notebook, 
            self.config,
            run_callback=self.on_tool_run
        )
        notebook.add(self.tools_panel, text='系统工具')
        
        # 环境变量面板
        self.env_panel = EnvPanel(notebook, self.config)
        notebook.add(self.env_panel, text='环境变量')
        
        # 状态栏
        self.status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, padx=5, pady=2)
        
        # 在工具栏添加关于按钮
        about_btn = ttk.Button(
            toolbar,
            text="关于",
            command=self.show_about,
            width=8
        )
        about_btn.pack(side=tk.RIGHT, padx=5)

    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, sticky='ew', padx=5, pady=(0,5))
        
        # 设置样式
        style = ttk.Style()
        style.configure("Toolbar.TButton", padding=3)
        style.configure("Toolbar.TCombobox", padding=3)
        
        # 最近使用下拉框
        self.recent_combo = ttk.Combobox(
            toolbar, 
            width=20,
            style="Toolbar.TCombobox",
            state='readonly'
        )
        self.recent_combo.grid(row=0, column=0, padx=(0,5))
        self.recent_combo.set('最近使用')
        self.recent_combo.bind('<<ComboboxSelected>>', self.on_recent_selected)
        
        # 工具栏按钮
        ttk.Button(
            toolbar, 
            text="刷新",
            style="Toolbar.TButton",
            command=self.refresh_all
        ).grid(row=0, column=1, padx=2)
        
        ttk.Button(
            toolbar,
            text="设置",
            style="Toolbar.TButton", 
            command=self.show_settings
        ).grid(row=0, column=2, padx=2)
        
        # 加载头像图片
        try:
            tx_img = Image.open(IMAGES_DIR / "tx.png")
            # 设置头像大小为24x24像素
            tx_size = (24, 24)
            tx_img.thumbnail(tx_size, Image.Resampling.LANCZOS)
            self.tx_photo = ImageTk.PhotoImage(tx_img)
            
            # 创建头像按钮
            about_btn = ttk.Label(
                toolbar, 
                image=self.tx_photo,
                cursor="hand2"  # 鼠标悬停时显示手型光标
            )
            about_btn.grid(row=0, column=3, padx=2)
            about_btn.bind("<Button-1>", lambda e: self.show_about())  # 绑定点击事件
            
            # 添加工具提示
            ToolTip(about_btn, "关于者")
            
        except Exception as e:
            # 如果加载图片失败，使用文字按钮作为后备
            self.logger.error(f"加载头像失败: {e}")
            about_btn = ttk.Button(
                toolbar,
                text="关于",
                style="Toolbar.TButton",
                command=self.show_about
            )
            about_btn.grid(row=0, column=3, padx=2)

    def create_statusbar(self):
        """创建状态栏"""
        statusbar = ttk.Frame(self.root, style="Statusbar.TFrame")
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 状态信息标签
        self.status_label = ttk.Label(
            statusbar,
            text="就绪",
            style="Statusbar.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 版本和作者信息
        info_label = ttk.Label(
            statusbar,
            text="v1.0.0 | 作者：豆子 | 公众号：豆子爱分享",
            style="Statusbar.TLabel"
        )
        info_label.pack(side=tk.RIGHT, padx=5)

    def run_system_tool(self, command):
        """运行系统工具"""
        try:
            logging.info(f"正在运行工具: {command}")
            return run_system_tool(command)
        except Exception as e:
            logging.error(f"运行工具时出错: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    def on_tool_run(self, name: str, command: str):
        """工具运行回调函数"""
        try:
            # 更新最近使用的工具列表
            if name not in self.recent_tools:
                self.recent_tools.insert(0, name)
                if len(self.recent_tools) > self.max_recent:
                    self.recent_tools.pop()
            
            # 更新下拉框
            self.recent_combo['values'] = self.recent_tools
            
        except Exception as e:
            self.logger.error(f"更新最近使用工具失败: {str(e)}")

    def add_to_recent(self, tool_name: str, command: str):
        """添加工具到最近使用列表"""
        if not hasattr(self, 'recent_tools'):
            self.recent_tools = []
            
        # 移除已存在的相同工具
        self.recent_tools = [t for t in self.recent_tools 
                           if t['name'] != tool_name]
        
        # 添加到列表开头
        self.recent_tools.insert(0, {
            'name': tool_name,
            'command': command
        })
        
        # 保持列表长度不超过最大值
        self.recent_tools = self.recent_tools[:self.max_recent]
        
        # 更新下拉菜单
        self.update_recent_tools()

    def update_recent_tools(self):
        """更新最近使用工具下拉菜单"""
        if not self.recent_tools:
            self.recent_combo['values'] = ['无最近使用记录']
        else:
            self.recent_combo['values'] = [t['name'] for t in self.recent_tools]
        self.recent_combo.set('最近使用')

    def on_recent_selected(self, event):
        """处理最近使用工具选择事件"""
        selection = self.recent_combo.get()
        if selection and selection != '无最近使用记录' and selection != '最近使用':
            tool = next((t for t in self.recent_tools if t['name'] == selection), None)
            if tool:
                self.run_system_tool(tool['command'])
        self.recent_combo.set('最近使用')

    def refresh_all(self):
        """刷新所有面板"""
        try:
            self.env_panel.update_backup_list()
            self.status_label.config(text="刷新完成")
        except Exception as e:
            self.logger.error(f"刷新失败: {str(e)}")
            self.status_label.config(text="刷新失败")

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.root, self.config)
        dialog.grab_set()  # 模态显示

    def show_about(self):
        """显示关于对话框"""
        about_text = """系统环境管理工具 v1.0.0
        
用于管理Windows系统环境变量和系统工具的集成工具。

功能特点：
- 系工具快速访问
- 环境变量备份和恢复
- 全盘环境路径扫描
- 最近使用工具记录

作者：豆子
公众号：豆子爱分享
版权所有 2024"""
        
        messagebox.showinfo("关于", about_text)

    def cleanup(self):
        """清理资源"""
        try:
            # 清理扫描器资源
            if hasattr(self, 'env_panel'):
                self.env_panel.env_scanner._clean_resources()
            
            # 保存配置
            if hasattr(self, 'config'):
                self.config.save()
            
            # 关闭日志处理器
            for handler in logging.getLogger().handlers[:]:
                handler.close()
                logging.getLogger().removeHandler(handler)
            
        except Exception as e:
            logging.error(f"清理资源时出错: {str(e)}")

    def on_closing(self):
        """窗口关闭时的回调函数"""
        self.cleanup()  # 清理资源
        self.root.destroy()  # 直接关闭窗口

    def run(self):
        """运行主窗口"""
        try:
            self.logger.info("开运行主窗口...")
            # 确保窗口在最前面
            self.root.lift()
            self.root.focus_force()
            # 运行主循环
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"运行主窗口时出错: {str(e)}")
            raise

    def apply_theme(self):
        """应用统一主题"""
        try:
            style = ttk.Style()
            
            # 配置基本样式
            for widget, cfg in WIDGET_STYLES.items():
                style.configure(widget, **cfg)
                
            # 配置悬停效果
            style.map('TButton',
                background=[('active', UNIFIED_THEME['hover_bg'])],
                foreground=[('active', UNIFIED_THEME['button_fg'])]
            )
            
            # 配置文本控件
            for widget in self.root.winfo_children():
                if isinstance(widget, (tk.Text, tk.Listbox)):
                    widget.configure(
                        background=UNIFIED_THEME['entry_bg'],
                        foreground=UNIFIED_THEME['foreground'],
                        selectbackground=UNIFIED_THEME['select_bg'],
                        selectforeground=UNIFIED_THEME['select_fg']
                    )
                    
        except Exception as e:
            self.logger.error(f"应用主题失败: {str(e)}")

    def apply_font(self, *args):
        """应用字体设置"""
        try:
            size = int(self.font_var.get())
            style = ttk.Style()
            
            # 更新所有控件的字体
            default_font = ('微软雅黑', size)
            style.configure(".", font=default_font)
            style.configure("TLabel", font=default_font)
            style.configure("TButton", font=default_font)
            style.configure("Treeview", font=default_font)
            
            # 更新状态栏字体
            if hasattr(self, 'status_label'):
                self.status_label.configure(font=default_font)
                
            # 保存设置
            self.config.font_size = size
            self.config.save()
            
        except Exception as e:
            self.logger.error(f"应用字体失败: {str(e)}")

    def create_help_area(self):
        """创建使用说明区域"""
        try:
            help_frame = ttk.LabelFrame(self.root, text="使用说明")
            help_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 使用resource_path获取图片路径
            image_path = resource_path('data/images/gzh.png')
            if os.path.exists(image_path):
                img = Image.open(image_path)
                photo = ImageTk.PhotoImage(img)
                label = ttk.Label(help_frame, image=photo)
                label.image = photo  # 保持引用
                label.pack(pady=5)
            else:
                self.logger.warning(f"图片文件不存在: {image_path}")
                
        except Exception as e:
            self.logger.error(f"创建使用说明区域失败: {str(e)}")
