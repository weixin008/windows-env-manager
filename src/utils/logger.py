import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
import tkinter as tk

class GuiLogHandler(logging.Handler):
    """GUI日志处理器"""
    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget
        
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
        self.text_widget.after(0, append)

class LogManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        self.gui_handler = None
        
    def init_logging(self, log_dir: Path) -> bool:
        """初始化日志系统"""
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f'app.log'
            
            # 配置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            
            # 文件处理器
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
            )
            root_logger.addHandler(file_handler)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(levelname)s: %(message)s')
            )
            root_logger.addHandler(console_handler)
            
            return True
        except Exception as e:
            print(f"初始化日志系统失败: {str(e)}")
            return False
            
    def add_gui_handler(self, text_widget: tk.Text):
        """添加GUI日志处理器"""
        if self.gui_handler:
            return
            
        self.gui_handler = GuiLogHandler(text_widget)
        self.gui_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(self.gui_handler)
