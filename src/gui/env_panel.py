import tkinter as tk
import traceback
from tkinter import ttk, messagebox
import logging
from typing import Optional, Dict, List
from src.core.env_backup import EnvBackup
from src.core.env_scanner import EnvScanner
from src.utils.config import Config
from src.utils.admin import ensure_admin
from src.core.env_manager import EnvManager
from pathlib import Path
import os
import subprocess
from PIL import Image, ImageTk
import threading

class EnvPanel(ttk.Frame):
    def __init__(self, parent: ttk.Frame, config: Config):
        """初始化环境管理面板
        
        Args:
            parent: 父级窗口
            config: 配置对象
        """
        super().__init__(parent)
        self.config = config
        self.logger = logging.getLogger('EnvPanel')
        self.root = self.winfo_toplevel()  # 获取根窗口引用
        
        # 初始化组件
        self.env_backup = EnvBackup(config)
        self.env_scanner = EnvScanner()
        self.env_manager = EnvManager()
        
        # 初始化 backups 列表
        self.backups = []
        self.restore_thread = None
        
        # 配置网格权重
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 创建界面
        self.setup_ui()

    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧面板 - 备份和操作区域
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # 备份列表区域
        backup_frame = ttk.LabelFrame(left_frame, text="环境备份")
        backup_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.backup_listbox = tk.Listbox(backup_frame, height=8)
        self.backup_listbox.pack(fill=tk.X, padx=5, pady=5)
        
        # 备份操作按钮
        backup_btn_frame = ttk.Frame(backup_frame)
        backup_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 主要操作按钮
        self.backup_buttons = []  # 存储需要在操作时禁用的按钮
        
        self.create_backup_button = ttk.Button(backup_btn_frame, text="创建备份", command=self.create_backup)
        self.create_backup_button.pack(side=tk.LEFT, padx=2)
        self.backup_buttons.append(self.create_backup_button)
        
        self.restore_backup_button = ttk.Button(backup_btn_frame, text="恢复备份", command=self.restore_backup)
        self.restore_backup_button.pack(side=tk.LEFT, padx=2)
        self.backup_buttons.append(self.restore_backup_button)
        
        self.delete_backup_button = ttk.Button(backup_btn_frame, text="删除备份", command=self.delete_backup)
        self.delete_backup_button.pack(side=tk.LEFT, padx=2)
        self.backup_buttons.append(self.delete_backup_button)
        
        # 打开备份位置按钮（单独放置，不加入backup_buttons列表）
        location_btn = ttk.Button(backup_btn_frame, text="打开备份位置", command=self.open_backup_location)
        location_btn.pack(side=tk.RIGHT, padx=2)
        
        # 环境变量设置区域
        env_frame = ttk.LabelFrame(left_frame, text="环境变量管理入口")
        env_frame.pack(fill=tk.X, pady=5)

        # 添加说明文本
        ttk.Label(env_frame, 
            text="点击下方按钮打开系统环境变量设置",
            wraplength=200
            ).pack(fill=tk.X, padx=5, pady=5)

        # 打开环境变量设置按钮
        ttk.Button(
            env_frame, 
            text="打开环境变量设置", 
            command=self.open_env_settings
        ).pack(padx=5, pady=5)
        
        # 右侧面板 - 扫描结果区域
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 扫描控制区域
        scan_control_frame = ttk.Frame(right_frame)
        scan_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(scan_control_frame, text="开始扫描", command=self.start_full_scan).pack(side=tk.LEFT, padx=5)
        self.scan_progress = ttk.Progressbar(scan_control_frame, length=200, mode='determinate')
        self.scan_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 扫描结果显示区域
        result_frame = ttk.LabelFrame(right_frame, text="扫描结果")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 使用Text组件显示结果，添加滚动条
        self.scan_result = tk.Text(result_frame, wrap=tk.WORD, width=50, height=20)
        result_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.scan_result.yview)
        
        self.scan_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        self.scan_result.configure(yscrollcommand=result_scrollbar.set)
        
        # 初始化时更新备份列表
        self.update_backup_list()

    def create_backup(self):
        """创建环境变量备份"""
        try:
            if not ensure_admin():
                messagebox.showerror("错误", "需要管理员权限来创建环境变量备份")
                return
            
            description = "手动备份"
            backup_path = self.env_backup.create_backup(description)
            
            if backup_path:
                self.update_backup_list()
                messagebox.showinfo("成功", f"环境变量已备份到:\n{backup_path}")
            else:
                messagebox.showerror("错误", "创建备份失败")
                
        except Exception as e:
            self.logger.error(f"创建备份失败: {str(e)}")
            messagebox.showerror("错误", f"创建备份失败: {str(e)}")

    def restore_backup(self):
        """恢复备份"""
        selection = self.backup_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要恢复的备份")
            return
        
        backup = self.backups[selection[0]]
        backup_path = backup['path']
        
        if not messagebox.askyesno("确认", "确定要恢复此备份吗？"):
            return
        
        try:
            # 禁用相关按钮
            self.disable_buttons()
            
            def update_status(status_message):
                """更新状态显示的回调函数"""
                self.logger.debug(f"状态更新: {status_message}")
                
                # 确保在主线程中更新UI
                def update_ui():
                    try:
                        self.show_restore_progress(status_message)
                        
                        # 检查是否完成（成功或失败）
                        if "恢复成功" in status_message or "恢复失败" in status_message:
                            self.restore_complete("恢复成功" in status_message, 
                                               None if "恢复成功" in status_message else status_message)
                    except Exception as e:
                        self.logger.error(f"更新UI状态失败: {str(e)}")
                        # 确保出错时也启用按钮
                        self.enable_buttons()
                
                # 在主线程中执行UI更新
                if self.winfo_exists():  # 检查窗口是否还存在
                    self.after(0, update_ui)
            
            # 在新线程中执行恢复操作
            def restore_thread():
                try:
                    self.logger.debug("开始恢复线程")
                    success = self.env_backup.restore_backup(backup_path, update_status)
                    self.logger.debug(f"恢复操作完成，结果: {success}")
                    if not success:  # 如果restore_backup返回False但没有触发状态更新
                        self.after(0, lambda: self.restore_complete(False, "恢复操作失败"))
                except Exception as e:
                    self.logger.error(f"恢复线程异常: {str(e)}")
                    self.after(0, lambda: self.restore_complete(False, str(e)))
            
            # 启动恢复线程
            self.restore_thread = threading.Thread(target=restore_thread, daemon=True)
            self.restore_thread.start()
                
        except Exception as e:
            self.logger.error(f"启动恢复操作失败: {str(e)}")
            messagebox.showerror("错误", f"恢复备份失败: {str(e)}")
            self.enable_buttons()
            self.hide_restore_progress()

    def show_restore_progress(self, message):
        """显示恢复进度"""
        try:
            if not hasattr(self, 'restore_progress_label'):
                self.restore_progress_label = ttk.Label(self, text="")
                self.restore_progress_label.pack(pady=5)
            
            self.logger.debug(f"更新进度显示: {message}")
            self.restore_progress_label.configure(text=message)
            
            # 强制更新UI
            self.restore_progress_label.update()
            self.update_idletasks()
            
        except Exception as e:
            self.logger.error(f"显示进度信息失败: {str(e)}")

    def hide_restore_progress(self):
        """隐藏恢复进度"""
        try:
            if hasattr(self, 'restore_progress_label'):
                self.restore_progress_label.pack_forget()
                self.update_idletasks()
        except Exception as e:
            self.logger.error(f"隐藏进度信息失败: {str(e)}")

    def restore_complete(self, success, error_message=None):
        """恢复完成的回调"""
        try:
            self.logger.debug(f"恢复完成处理 - 成功: {success}, 错误: {error_message}")
            
            # 确保在主线程中执行
            def complete_ui():
                try:
                    # 无论成功失败都启用按钮
                    self.enable_buttons()
                    self.hide_restore_progress()
                    
                    if success:
                        messagebox.showinfo("成功", "恢复成功！\n如果环境仍未生效，建议重启后验证，如仍然未生效，可以点击右侧开始扫描，根据建议手动添加环境变量。")
                    else:
                        error_msg = f"恢复备份失败！\n{error_message if error_message else ''}"
                        messagebox.showerror("错误", error_msg)
                    
                    # 清理线程引用
                    self.restore_thread = None
                except Exception as e:
                    self.logger.error(f"完成UI更新失败: {str(e)}")
                    # 确保即使出错也启用按钮
                    self.enable_buttons()
            
            # 在主线程中执行UI更新
            if self.winfo_exists():  # 检查窗口是否还存在
                self.after(0, complete_ui)
                
        except Exception as e:
            self.logger.error(f"处理恢复完成回调失败: {str(e)}")
            messagebox.showerror("错误", "更新界面状态失败")
            # 确保出错时也启用按钮
            if self.winfo_exists():
                self.after(0, self.enable_buttons)

    def disable_buttons(self):
        """禁用操作按钮"""
        self.logger.debug("禁用所有操作按钮")
        for button in self.backup_buttons:
            button.configure(state='disabled')
        self.create_backup_button.configure(state='disabled')
        self.delete_backup_button.configure(state='disabled')

    def enable_buttons(self):
        """启用操作按钮"""
        self.logger.debug("启用所有操作按钮")
        for button in self.backup_buttons:
            button.configure(state='normal')
        self.create_backup_button.configure(state='normal')
        self.delete_backup_button.configure(state='normal')

    def update_backup_list(self):
        """更新备份列表"""
        try:
            # 清空列表框
            self.backup_listbox.delete(0, tk.END)
            # 获取新的备份列表
            self.backups = self.env_backup.get_backup_list()
            
            if not self.backups:
                self.backup_listbox.insert(tk.END, "暂无备份记录")
            else:
                # 更新列表框显示
                for backup in self.backups:
                    display_text = f"{backup['time']} - {backup['description']}"
                    self.backup_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            self.logger.error(f"更新备份列表失败: {str(e)}")
            self.backup_listbox.insert(tk.END, "加载备份列表失败")

    def start_full_scan(self):
        """开始全盘扫描"""
        try:
            self.scan_result.delete(1.0, tk.END)
            self.scan_progress['value'] = 0
            
            def update_progress(value):
                self.scan_progress['value'] = value
                
            self.env_scanner.set_progress_callback(update_progress)
            
            def scan_thread():
                error = None
                try:
                    results = self.env_scanner.scan()
                    self.after(0, lambda: self.update_scan_result(results))
                except Exception as scan_error:
                    error = scan_error
                    self.logger.error(f"扫描失败: {str(scan_error)}")
                    self.after(0, lambda: messagebox.showerror("错误", f"扫描失败: {str(scan_error)}"))
                finally:
                    self.after(0, lambda: self.scan_progress.configure(value=100))
            
            import threading
            threading.Thread(target=scan_thread, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"启动扫描失败: {str(e)}")
            messagebox.showerror("错误", f"启动扫描失败: {str(e)}")

    def update_scan_result(self, results: Dict[str, List[Dict]]):
        try:
            self.scan_result.delete(1.0, tk.END)
            if not results:
                self.scan_result.insert(tk.END, "未找到任何环境安装\n")
                return
            
            # 配置标签样式
            self.scan_result.tag_configure("heading", font=("TkDefaultFont", 9, "bold"))
            self.scan_result.tag_configure("version", font=("TkDefaultFont", 9))
            self.scan_result.tag_configure("active_version", font=("TkDefaultFont", 9, "bold"), foreground="green")
            self.scan_result.tag_configure("recommendation_header", font=("TkDefaultFont", 9, "bold"))
            self.scan_result.tag_configure("normal", font=("TkDefaultFont", 9))
            
            for tool, installations in results.items():
                self.scan_result.insert(tk.END, f"\n=== {tool} 环境检测结果 ===\n", "heading")
                
                # 检查当前激活的版本
                active_version = next((install['version'] for install in installations if any(status['exists'] and status['in_path'] for status in install['env_status'].values())), None)
                    
                # 显示当前系统配置的版本
                if active_version:
                    self.scan_result.insert(tk.END, f"\n当前系统配置版本: {active_version}\n", "active_version")
                
                # 显示所有安装的版本
                for install in installations:
                    version = install['version']
                    self.scan_result.insert(tk.END, f"\n版本: {version}\n", "version")
                    install_path = Path(install['install_path'])
                    self.scan_result.insert(tk.END, f"安装目录：{install_path}\n", "normal")
                    
                    # 显示bin目录
                    for bin_path in install['bin_paths']:
                        bin_full_path = install_path / bin_path if bin_path else install_path
                        if bin_full_path.exists():
                            self.scan_result.insert(tk.END, f"可执行文件目录：{bin_full_path}\n", "normal")
                
                # 显示建议
                self.scan_result.insert(tk.END, "\n使用建议：\n", "recommendation_header")
                if active_version:
                    self.scan_result.insert(tk.END, f"系统已正确配置 {tool} {active_version}，可以正常使用。\n", "normal")
                # 添加优化建议
                if installations and 'recommendations' in installations[0]:
                    optimization_recommendations = [r for r in installations[0]['recommendations'] if not any(env in r for env in installations[0]['env_status'].keys())]
                    if optimization_recommendations:
                        self.scan_result.insert(tk.END, "\n优化建议：\n", "recommendation_header")
                        for recommendation in optimization_recommendations:
                            self.scan_result.insert(tk.END, f"{recommendation}\n", "normal")
                else:
                    if installations and 'recommendations' in installations[0]:
                        for recommendation in installations[0]['recommendations']:
                            self.scan_result.insert(tk.END, f"{recommendation}\n", "normal")
                
                self.scan_result.insert(tk.END, "\n" + "="*50 + "\n")
                
        except Exception as e:
            self.logger.error(f"更新扫描结果失败: {str(e)}")
            messagebox.showerror("错误", f"更新扫描结果失败: {str(e)}")

    def delete_backup(self):
        """删除选中的备份"""
        try:
            selection = self.backup_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择要删除的备份文件")
                return
            
            # 直接从self.backups获取备份信息
            backup = self.backups[selection[0]]
            backup_path = backup['path']
            
            if messagebox.askyesno("确认", "确定要删除选中的备份文件吗？"):
                if self.env_backup.delete_backup(backup_path):
                    self.update_backup_list()
                    messagebox.showinfo("成功", "备份文件已删除")
                else:
                    messagebox.showerror("错误", "删除备份失败")
                
        except Exception as e:
            self.logger.error(f"删除备份失败: {str(e)}")
            messagebox.showerror("错误", f"删除备份失败: {str(e)}")

    def set_env_var(self):
        """设置环境变量"""
        try:
            if not ensure_admin():
                messagebox.showerror("错误", "需要管理员权限来修改环境变量")
                return
            
            name = self.var_name.get().strip()
            value = self.var_value.get().strip()
            
            if not name:
                messagebox.showwarning("警告", "请输入变量名")
                return
            
            if not value:
                messagebox.showwarning("警告", "请输入变量值")
                return
            
            if self.env_manager.set_system_env(name, value):
                messagebox.showinfo("成功", f"环境变量 {name} 已设置")
            else:
                messagebox.showerror("错误", "设置环境变量失败")
                
        except Exception as e:
            self.logger.error(f"设置环境变量失败: {str(e)}")
            messagebox.showerror("错误", f"设置环境变量失败: {str(e)}")

    def delete_env_var(self):
        """删除环境变量"""
        try:
            if not ensure_admin():
                messagebox.showerror("错误", "需要管理员权限来删除环境变量")
                return
            
            name = self.var_name.get().strip()
            if not name:
                messagebox.showwarning("警告", "请输入要删除的变量名")
                return
            
            if messagebox.askyesno("确认", f"确定要删除环境变量 {name} 吗？"):
                if self.env_manager.delete_system_env(name):
                    messagebox.showinfo("成功", f"环境变量 {name} 已删除")
                else:
                    messagebox.showerror("错误", "删除环境变量失败")
                
        except Exception as e:
            self.logger.error(f"删除环境变量失败: {str(e)}")
            messagebox.showerror("错误", f"删除环境变量失败: {str(e)}")

    def refresh_path(self):
        """刷新 PATH 环境变量"""
        try:
            if not ensure_admin():
                messagebox.showerror("错误", "需要管理员权限来刷新PATH")
                return
            
            if self.env_manager.refresh_path():
                messagebox.showinfo("成功", "PATH 环境变量已刷新")
            else:
                messagebox.showerror("错误", "刷新 PATH 失败")
                
        except Exception as e:
            self.logger.error(f"刷新 PATH 失败: {str(e)}")
            messagebox.showerror("错误", f"刷新 PATH 失败: {str(e)}")

    def scan_environments(self):
        """扫描环境"""
        try:
            # 开始扫描
            scanner = EnvScanner()
            results = scanner.scan()
            
            # 更新扫描结果显示
            self.update_scan_result(results)
            
        except Exception as e:
            self.logger.error(f"扫描失败: {str(e)}", exc_info=True)
            error_msg = str(e)
            self.after(0, lambda error=error_msg: messagebox.showerror("错误", f"扫描失败: {error}"))

    def open_env_settings(self):
        """打开环境变量设置"""
        try:
            # 使用异步方式启动系统命令
            subprocess.Popen('rundll32.exe sysdm.cpl,EditEnvironmentVariables')
        except Exception as e:
            self.logger.error(f"打开环境变量设置失败: {str(e)}")
            messagebox.showerror("错误", f"打开环境变量设置失败: {str(e)}")

    def open_backup_location(self):
        """打开备份文件所在目录"""
        try:
            backup_dir = self.config.get_backup_dir()
            if not backup_dir.exists():
                backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用系统默认文件管理器打开目录
            os.startfile(str(backup_dir))
        except Exception as e:
            self.logger.error(f"打开备份位置失败: {str(e)}")
            messagebox.showerror("错误", f"无法打开备份位置: {str(e)}")
