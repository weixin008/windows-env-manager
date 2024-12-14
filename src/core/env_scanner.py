import os
from pathlib import Path
import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Dict, List, Tuple, Optional, Callable
import time
import json
import hashlib
from datetime import datetime, timedelta
import threading
from queue import Queue
import fnmatch
import subprocess
from src.utils.resource import resource_path

class EnvScanner:
    def __init__(self):
        self.logger = logging.getLogger('EnvScanner')
        self.progress_callback = None
        
        try:
            # 使用resource_path获取配置文件路径
            config_path = resource_path('data/scan_config.json')
            if not os.path.exists(config_path):
                self.logger.error(f"配置文件不存在: {config_path}")
                self.scan_config = {}  # 使用空配置
                return
                
            with open(config_path, 'r', encoding='utf-8') as f:
                self.scan_config = json.load(f)
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            self.scan_config = {}  # 使用空配置

    def scan(self) -> Dict[str, List[Dict]]:
        """扫描系统中已安装的开发工具"""
        results = {}
        scanned_paths = set()  # 用于记录已扫描的路径
        
        # 获取所有可用的磁盘驱动器
        drives = [Path(f"{d}:\\") for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' 
                 if os.path.exists(f"{d}:\\")]
        
        self.logger.debug(f"开始扫描驱动器: {[str(d) for d in drives]}")
        
        for tool_name, tool_config in self.scan_config.items():
            installations = []
            for drive in drives:
                self.logger.debug(f"正在扫描驱动器 {drive} 中的 {tool_name}")
                found = self._scan_tool(drive, tool_name, tool_config, scanned_paths)
                if found:
                    installations.extend(found)
            
            if installations:
                results[tool_name] = installations
                
        return results

    def _scan_tool(self, drive: Path, tool_name: str, tool_config: Dict, 
                   scanned_paths: set) -> List[Dict]:
        installations = []
        
        try:
            # 排除的目录模式
            exclude_patterns = [
                "*demo*",
                "*__pycache__*",
                "*tools*",
                "*test*",
                "*examples*"
            ]
            
            # 添加根目录Python搜索模式
            root_patterns = ["Python*"] if tool_name == "Python" else []
            
            def should_scan_dir(path: str) -> bool:
                if tool_name != "Python":
                    return True
                return not any(fnmatch.fnmatch(path.lower(), ex.lower()) for ex in exclude_patterns)
            
            # 扫描函数
            def scan_path(path: Path):
                if str(path) in scanned_paths:  # 检查路径是否已扫描
                    return
                
                if path.is_dir() and should_scan_dir(str(path)):
                    installation = self._analyze_installation(path, tool_name, tool_config)
                    if installation:
                        installations.append(installation)
                        scanned_paths.add(str(path))  # 记录已扫描的路径
            
            # 扫描配置的路径
            for path in tool_config['paths']:
                full_path = drive / path
                if '*' in str(path):
                    for matched_path in drive.glob(path):
                        scan_path(matched_path)
                else:
                    if full_path.exists():
                        scan_path(full_path)
            
            # 扫描根目录
            for pattern in root_patterns:
                for matched_path in drive.glob(pattern):
                    scan_path(matched_path)
                        
        except Exception as e:
            self.logger.error(f"扫描 {tool_name} 路径时出错: {str(e)}")
            
        return installations

    def _analyze_installation(self, path: Path, tool_name: str, tool_config: Dict) -> Optional[Dict]:
        """分析工具安装并返回详细信息"""
        try:
            self.logger.debug(f"正在分析路径: {path}")
            
            # 检查bin路径
            bin_paths = []
            for bin_path in tool_config['bin_paths']:
                full_bin_path = path / bin_path
                if full_bin_path.is_dir():
                    bin_paths.append(str(full_bin_path))
                    self.logger.debug(f"找到bin路径: {full_bin_path}")

            if not bin_paths:
                self.logger.debug(f"未在 {path} 找到有效的bin路径")
                return None

            # 获取版本信息
            version = self._get_version(tool_name, bin_paths[0], tool_config)
            self.logger.debug(f"获取到版本信息: {version}")
            
            # 检查环境变量
            env_status = self._check_env_vars(tool_config['env_vars'], bin_paths)
            self.logger.debug(f"环境变量状态: {env_status}")
            
            result = {
                'name': tool_name,
                'install_path': str(path),
                'bin_paths': bin_paths,
                'version': version,
                'env_status': env_status,
                'recommendations': self._generate_recommendations(
                    tool_name, bin_paths, env_status
                )
            }
            
            self.logger.debug(f"分析结果: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"分析 {tool_name} 安装时出错: {str(e)}")
            return None

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def _update_progress(self, value):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(value)

    def _get_version(self, tool_name: str, bin_path: str, tool_config: Dict) -> str:
        """获取工具版本信息"""
        try:
            version_cmd = tool_config.get('version_cmd')
            if not version_cmd:
                return "未知版本"
            
            # 分割命令和参数
            cmd_parts = version_cmd.split()
            cmd = str(Path(bin_path) / cmd_parts[0])
            args = cmd_parts[1:]
            
            # 执行版本命令
            result = subprocess.run([cmd] + args, 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8',
                                  errors='ignore',
                                  shell=True)  # 添加shell=True以处理某些特殊命令
            
            # 特殊处理某些工具的版本输出
            if tool_name == "Java":
                # Java输出在stderr中，格式如: java version "1.8.0_301"
                version_line = result.stderr.split('\n')[0] if result.stderr else ""
                match = re.search(r'version "([^"]+)"', version_line)
                return match.group(1) if match else "未知版本"
            
            elif tool_name == "Python":
                # Python输出格式: Python 3.8.0
                version_line = result.stdout.strip()
                match = re.search(r'Python (\d+\.\d+\.\d+)', version_line)
                return match.group(1) if match else "未知版本"
            
            elif tool_name == "Node.js":
                # Node输出格式: v14.17.0
                version_line = result.stdout.strip()
                return version_line.lstrip('v')
            
            elif tool_name == "Git":
                # Git输出格式: git version 2.35.1.windows.2
                version_line = result.stdout.strip()
                match = re.search(r'git version (\S+)', version_line)
                return match.group(1) if match else "未知版本"
            
            # 其他工具尝试提取版本号
            version_line = result.stdout.strip() or result.stderr.strip()
            # 尝试匹配版本号模式
            match = re.search(r'(\d+\.\d+\.\d+)', version_line)
            return match.group(1) if match else version_line.split('\n')[0]
            
        except Exception as e:
            self.logger.error(f"获取{tool_name}版本失败: {str(e)}")
            return "未知版本"

    def _check_env_vars(self, env_vars: List[str], bin_paths: List[str]) -> Dict:
        """检查环境变量状态"""
        try:
            env_status = {}
            current_env = os.environ
            
            for var in env_vars:
                env_status[var] = {
                    'exists': var in current_env,
                    'value': current_env.get(var, ''),
                    'in_path': any(
                        bp in current_env.get('Path', '').split(';')
                        for bp in bin_paths
                    )
                }
            return env_status
            
        except Exception as e:
            self.logger.error(f"检查环境变量状态失败: {str(e)}")
            return {}

    def _generate_recommendations(self, tool_name: str, bin_paths: List[str], env_status: Dict) -> List[str]:
        """生成环境配置建议"""
        recommendations = []
        
        try:
            # 获取配置文件中的建议
            tool_config = self.scan_config.get(tool_name, {})
            config_recommendations = tool_config.get('recommendations', [])
            
            # 检查环境变量
            for var, status in env_status.items():
                if not status['exists'] or not status['value']:
                    var_recommendation = next(
                        (r for r in config_recommendations if var in r),
                        f"建议设置 {var} 环境变量"
                    )
                    recommendations.append(var_recommendation)
            
            # 检查 PATH
            for bin_path in bin_paths:
                if not any(bin_path in path for path in os.environ.get('Path', '').split(';')):
                    path_recommendation = next(
                        (r for r in config_recommendations if 'PATH' in r and bin_path in r),
                        f"建议将 {bin_path} 添加到 PATH 环境变量"
                    )
                    recommendations.append(path_recommendation)
            
            # 添加其他配置建议
            other_recommendations = [r for r in config_recommendations 
                                   if not any(var in r for var in env_status.keys()) 
                                   and 'PATH' not in r]
            recommendations.extend(other_recommendations)
            
            # 去重
            recommendations = list(dict.fromkeys(recommendations))
            
            if not recommendations:
                recommendations.append("当前环境配置正常，无需调整")
                
            return recommendations
                
        except Exception as e:
            self.logger.error(f"生成建议失败: {str(e)}")
            return ["生成建议时发生错误"]

    def _scan_wildcard_path(self, drive: Path, pattern: str, tool_name: str, tool_config: Dict) -> List[Dict]:
        """处理通配符路径的扫描"""
        installations = []
        try:
            # 确保使用相对路径模式
            pattern = pattern.replace('\\', '/')
            if pattern.startswith('/'):
                pattern = pattern[1:]
            
            # 将驱动器路径作为基础目录
            base_dir = drive
            
            if '**' in pattern:
                # 处理递归模式
                parts = pattern.split('**')
                base_pattern = parts[0].rstrip('/')
                search_pattern = parts[1].lstrip('/')
                
                # 先查找基础目录
                for base_path in base_dir.glob(base_pattern):
                    if base_path.is_dir():
                        # 在基础目录下递归索
                        for path in base_path.rglob(search_pattern):
                            if path.is_dir():
                                installation = self._analyze_installation(path, tool_name, tool_config)
                                if installation:
                                    installations.append(installation)
            else:
                # 处理简单的通配符模式
                for path in base_dir.glob(pattern):
                    if path.is_dir():
                        installation = self._analyze_installation(path, tool_name, tool_config)
                        if installation:
                            installations.append(installation)
                    
        except Exception as e:
            self.logger.error(f"通符路径扫描失败 {pattern}: {str(e)}")
            
        return installations

    def _is_potential_tool_dir(self, dir_name: str, tool_name: str) -> bool:
        """判断目录名是否可能是工具安装目录"""
        dir_lower = dir_name.lower()
        tool_lower = tool_name.lower()
        
        # 工具特定的关键字
        tool_keywords = {
            "Java": ["java", "jdk", "jre"],
            "Python": ["python", "py"],
            "Node.js": ["node", "npm", "nodejs"],
            "FFmpeg": ["ffmpeg", "ff"],
            "MySQL": ["mysql", "mariadb"],
            "Maven": ["maven", "mvn"],
            "Go": ["go", "golang"],
            "Gradle": ["gradle"],
            "Ruby": ["ruby", "rb"],
            "PHP": ["php"],
            "Android SDK": ["android", "sdk"],
            "Visual Studio Code": ["vscode", "code"],
            "Docker": ["docker"],
            "MongoDB": ["mongodb", "mongo"],
            "PostgreSQL": ["postgresql", "pgsql", "postgres"],
            "Nginx": ["nginx"],
            "Rust": ["rust", "cargo", "rustup"],
        }
        
        keywords = tool_keywords.get(tool_name, [tool_lower])
        return any(keyword in dir_lower for keyword in keywords)

    def _get_ffmpeg_version(self, bin_path: Path) -> str:
        """获取 FFmpeg 版本信息"""
        try:
            result = subprocess.run([str(bin_path / 'ffmpeg'), '-version'], 
                                  capture_output=True, text=True)
            # 只获取第一行的版本信息
            version_line = result.stdout.split('\n')[0]
            return version_line
        except Exception:
            return "未知版本"

    def _get_docker_version(self, bin_path: Path) -> str:
        """获取 Docker 版本信息"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, encoding='utf-8')
            if result.returncode == 0:
                return result.stdout.strip()
            return "未知版本"
        except Exception as e:
            self.logger.error(f"获取 Docker 版本失败: {str(e)}")
            return "未知版本"
