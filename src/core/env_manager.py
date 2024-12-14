import winreg
import os
import json
import datetime
import ctypes
from pathlib import Path
import logging

class EnvManager:
    def __init__(self):
        self.system_root = winreg.HKEY_LOCAL_MACHINE
        self.env_key = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        self._keys = []  # 跟踪打开的注册表键
        
        # 配置日志
        self.logger = logging.getLogger('EnvManager')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # 文件处理器
            fh = logging.FileHandler('env_manager.log', encoding='utf-8')
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def __del__(self):
        """确保所有注册表键都被正确关闭"""
        self._close_all_keys()

    def _close_all_keys(self):
        """关闭所有打开的注册表键"""
        for key in self._keys:
            try:
                winreg.CloseKey(key)
                self.logger.debug(f"关闭注册表键: {key}")
            except Exception as e:
                self.logger.error(f"关闭注册表键失败: {str(e)}")
        self._keys.clear()

    def get_system_env(self):
        """获取系统环境变量"""
        key = None
        try:
            key = winreg.OpenKey(self.system_root, self.env_key, 0, winreg.KEY_READ)
            self._keys.append(key)
            self.logger.info("开始读取系统环境变量")
            
            env_dict = {}
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    env_dict[name] = value
                    i += 1
                except WindowsError:
                    break  # 没有更多的值可以枚举
                
            self.logger.info(f"成功读取 {len(env_dict)} 个环境变量")
            return env_dict
        except Exception as e:
            error_msg = f"获取系统环境变量失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            if key:
                try:
                    winreg.CloseKey(key)
                    self._keys.remove(key)
                except Exception as e:
                    self.logger.error(f"关闭注册表键失败: {str(e)}")

    def update_env_var(self, name, value):
        """更新系统环境变量"""
        if not name or not isinstance(name, str):
            raise ValueError("环境变量名称无效")
            
        if not isinstance(value, str):
            raise ValueError("环境变量值必须是字符串类型")

        key = None
        try:
            key = winreg.OpenKey(self.system_root, self.env_key, 0, winreg.KEY_ALL_ACCESS)
            self._keys.append(key)
            self.logger.info(f"开始更新环境变量: {name} = {value}")
            
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            self.logger.info(f"成功更新环境变量: {name} = {value}")
        except Exception as e:
            error_msg = f"更新环境变量失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            if key:
                try:
                    winreg.CloseKey(key)
                    self._keys.remove(key)
                except Exception as e:
                    self.logger.error(f"关闭注册表键失败: {str(e)}")

    def refresh_path(self) -> bool:
        """刷新系统 PATH 环境变量"""
        try:
            # 获取当前 PATH
            current_path = self.get_system_env().get('Path', '')
            
            # 移除重复和无效路径
            path_list = []
            for p in current_path.split(';'):
                p = p.strip()
                if p and p not in path_list and os.path.exists(p):
                    path_list.append(p)
            
            # 重新组合 PATH
            new_path = ';'.join(path_list)
            
            # 更新注册表
            key = winreg.OpenKey(
                self.system_root,
                self.env_key,
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            
            # 广播环境变量更改消息
            import win32con
            import win32gui
            win32gui.SendMessage(
                win32con.HWND_BROADCAST,
                win32con.WM_SETTINGCHANGE,
                0,
                'Environment'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"刷新 PATH 失败: {str(e)}")
            return False

    def set_system_env(self, name: str, value: str) -> bool:
        """设置系统环境变量"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               'System\\CurrentControlSet\\Control\\Session Manager\\Environment', 
                               0, 
                               winreg.KEY_ALL_ACCESS) as key:
                winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
                
            # 通知系统环境变量已更改
            import win32con
            import win32gui
            win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')
            
            self.logger.info(f"成功设置系统环境变量: {name}={value}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置系统环境变量失败: {str(e)}")
            return False
