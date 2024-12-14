import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.config import Config

class HistoryManager:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger('HistoryManager')
        # 使用配置目录来存储历史记录
        self.history_file = self.config.app_dir / 'history.json'
        self.history: List[Dict] = self._load_history()
        
    def add_record(self, action: str, details: Dict) -> None:
        """添加操作记录
        
        Args:
            action: 操作类型
            details: 操作详情
        """
        try:
            record = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "details": details
            }
            self.history.append(record)
            self._save_history()
            self.logger.info(f"添加操作记录: {action}")
            
        except Exception as e:
            self.logger.error(f"添加操作记录失败: {str(e)}")
            
    def get_records(self, start_time: Optional[datetime] = None) -> List[Dict]:
        """获取操作记录
        
        Args:
            start_time: 开始时间,为None时返回所有记录
            
        Returns:
            List[Dict]: 操作记录列表
        """
        try:
            if not start_time:
                return self.history
                
            return [r for r in self.history 
                    if datetime.fromisoformat(r["timestamp"]) >= start_time]
                    
        except Exception as e:
            self.logger.error(f"获取操作记录失败: {str(e)}")
            return []
                
    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
            
        except Exception as e:
            self.logger.error(f"加载历史记录失败: {str(e)}")
            return []
        
    def _save_history(self) -> None:
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {str(e)}") 