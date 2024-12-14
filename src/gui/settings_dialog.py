import tkinter as tk
from tkinter import ttk
from ..utils.config import Config
import json

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config: Config):
        super().__init__(parent)
        self.config = config
        
        self.title("设置")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # 创建样式
        self.style = ttk.Style()
        
        # 创建界面
        self.create_widgets()
        
        # 居中显示
        self.center_window()
        
    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 主题设置页
        theme_frame = ttk.Frame(notebook, padding=10)
        notebook.add(theme_frame, text="主题设置")
        
        # 主题模式
        ttk.Label(theme_frame, text="主题模式:", font=('微软雅黑', 9, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        self.theme_mode = ttk.Combobox(theme_frame, values=['浅色模式', '深色模式'], state='readonly', width=20)
        self.theme_mode.grid(row=0, column=1, padx=10)
        self.theme_mode.set('浅色模式')
        
        # 字体设置
        ttk.Label(theme_frame, text="界面字体:", font=('微软雅黑', 9, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        self.font_family = ttk.Combobox(theme_frame, values=['微软雅黑', '宋体', 'Arial'], state='readonly', width=20)
        self.font_family.grid(row=1, column=1, padx=10)
        self.font_family.set('微软雅黑')
        
        # 字体大小
        ttk.Label(theme_frame, text="字体大小:", font=('微软雅黑', 9, 'bold')).grid(row=2, column=0, sticky='w', pady=5)
        self.font_size = ttk.Spinbox(theme_frame, from_=8, to=16, width=18)
        self.font_size.grid(row=2, column=1, padx=10)
        self.font_size.set(9)
        
        # 按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="应用", command=self.apply_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side=tk.RIGHT)
        
    def apply_settings(self):
        # 保存设置
        settings = {
            'theme': {
                'mode': self.theme_mode.get(),
                'font_family': self.font_family.get(),
                'font_size': int(self.font_size.get())
            }
        }
        
        self.config.save_settings(settings)
        self.apply_theme()
        self.destroy()
        
    def apply_theme(self):
        mode = self.theme_mode.get()
        if mode == '深色模式':
            self.style.configure('TFrame', background='#2b2b2b')
            self.style.configure('TLabel', background='#2b2b2b', foreground='#ffffff')
            self.style.configure('TButton', background='#3c3f41', foreground='#ffffff')
        else:
            self.style.configure('TFrame', background='#f0f0f0')
            self.style.configure('TLabel', background='#f0f0f0', foreground='#000000')
            self.style.configure('TButton', background='#e1e1e1', foreground='#000000') 