import os
import json
import logging
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.config import Config
from src.core.env_manager import EnvManager

class EnvBackup:
    def __init__(self, config: Config):
        self.config = config
        self.backup_dir = self.config.get_backup_dir()
        self.logger = logging.getLogger('EnvBackup')
        self.env_manager = EnvManager()
        
    def get_backup_list(self):
        """获取备份文件列表"""
        try:
            backups = []
            for file in self.backup_dir.glob('*.reg'):
                # 从文件名中提取时间和描述信息
                file_name = file.name
                # 解析文件名格式: env_backup_YYYYMMDD_HHMMSS_description.reg
                parts = file_name.replace('.reg', '').split('_')
                if len(parts) >= 4:
                    timestamp = f"{parts[2][:4]}-{parts[2][4:6]}-{parts[2][6:]} {parts[3][:2]}:{parts[3][2:4]}:{parts[3][4:]}"
                    description = '_'.join(parts[4:]) if len(parts) > 4 else '无描述'
                    backups.append({
                        'file': file_name,
                        'time': timestamp,
                        'description': description,
                        'path': str(file)
                    })
            
            # 按时间倒序排序
            return sorted(backups, key=lambda x: x['time'], reverse=True)
            
        except Exception as e:
            logging.error(f"获取备份列表失败: {str(e)}")
            return []

    def create_backup(self, description: str = "") -> Optional[Path]:
        """创建环境变量备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"env_backup_{timestamp}_{description}.reg"
            
            # 导出系统环境变量
            result = subprocess.run(
                ['reg', 'export', 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 
                 str(backup_file), '/y'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return backup_file
            else:
                raise RuntimeError(f"导出注册表失败: {result.stderr}")
                
        except Exception as e:
            logging.error(f"创建备份失败: {str(e)}")
            return None

    def delete_backup(self, backup_path: str) -> bool:
        """删除备份文件
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            backup_file = Path(backup_path)
            if backup_file.exists():
                backup_file.unlink()
                return True
            return False
        except Exception as e:
            logging.error(f"删除备份失败: {str(e)}")
            return False

    def restore_backup(self, backup_path, status_callback=None):
        """
        恢复备份
        :param backup_path: 备份文件路径
        :param status_callback: 状态回调函数
        :return: 是否成功
        """
        try:
            self.logger.debug(f"开始恢复备份: {backup_path}")
            
            def update_status(message):
                """更新状态的辅助函数"""
                self.logger.debug(f"状态更新: {message}")
                if status_callback:
                    try:
                        status_callback(message)
                    except Exception as e:
                        self.logger.error(f"状态回调失败: {str(e)}")

            update_status("正在导入注册表...")
            
            # 导入注册表
            if not self._import_reg(backup_path):
                update_status("恢复失败：注册表导入失败")
                return False
            
            self.logger.debug("注册表导入完成")
            
            # 异步发送环境变更广播（不等待响应）
            try:
                import win32con
                import win32gui
                win32gui.PostMessage(
                    win32con.HWND_BROADCAST,
                    win32con.WM_SETTINGCHANGE,
                    0,
                    'Environment'
                )
            except Exception as e:
                self.logger.warning(f"发送环境变更广播失败（不影响恢复结果）: {str(e)}")
            
            # 注册表导入成功就认为恢复成功
            update_status("恢复成功，如果环境仍未生效，建议重启后验证，如仍然未生效，可以点击右侧开始扫描，根据建议手动添加环境变量")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复备份失败: {str(e)}")
            if status_callback:
                try:
                    status_callback(f"恢复失败: {str(e)}")
                except:
                    pass
            return False

    def _validate_backup_file(self, backup_file: Path) -> bool:
        """验证备份文件的有效性"""
        try:
            # 检查文件大小
            if backup_file.stat().st_size == 0:
                self.logger.error("备份文件为空")
                return False

            # 检查文件格式（.reg文件应该以Windows Registry Editor Version开头）
            with open(backup_file, 'r', encoding='utf-16') as f:
                first_line = f.readline().strip()
                if not first_line.startswith('Windows Registry Editor Version'):
                    self.logger.error("无效的注册表文件格式")
                    return False

            return True
        except Exception as e:
            self.logger.error(f"验证备份文件失败: {str(e)}")
            return False

    def _import_reg(self, backup_path):
        """导入注册表文件"""
        try:
            result = subprocess.run(
                ['reg', 'import', backup_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.logger.info("注册表导入成功")
                return True
            else:
                error_msg = result.stderr or "未知错误"
                self.logger.error(f"注册表导入失败: {error_msg}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("注册表导入超时")
            return False
        except Exception as e:
            self.logger.error(f"注册表导入失败: {str(e)}")
            return False

    def _load_backup_data(self):
        # 加载备份数据的具体实现
        pass
        
    def _apply_backup(self):
        # 应用备份数据的具体实现
        pass
