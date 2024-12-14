import configparser
import os
import json
from pathlib import Path
from typing import Optional, Any
import logging

class Config:
    def __init__(self):
        self.font_size = 9
        self.font_family = "微软雅黑"
        self.window_size = (800, 600)
        self.app_data_dir = Path.home() / '.env_manager'
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加备份目录配置
        self.backup_dir = self.app_data_dir / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.load()
    
    def load(self):
        """加载配置"""
        try:
            config_path = self.app_data_dir / 'config.json'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.font_size = data.get('font_size', 9)
                    self.font_family = data.get('font_family', "微软雅黑")
                    self.window_size = data.get('window_size', (800, 600))
        except Exception as e:
            logging.error(f"加载配置失败: {str(e)}")
    
    def save(self):
        """保存配置"""
        try:
            config_path = self.app_data_dir / 'config.json'
            data = {
                'font_size': self.font_size,
                'font_family': self.font_family,
                'window_size': self.window_size
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存配置失败: {str(e)}")
    
    def get_backup_dir(self) -> Path:
        """获取备份目录路径"""
        return self.backup_dir
