import PyInstaller.__main__
import sys
import os

# 确保在项目根目录下运行
if not os.path.exists('src/main.py'):
    print("请在项目根目录下运行此脚本")
    sys.exit(1)

PyInstaller.__main__.run([
    'src/main.py',                     # 主程序
    '--name=EnvManager',               # 生成的exe名称
    '--onefile',                       # 打包成单个文件
    '--windowed',                      # 使用GUI模式
    '--icon=data/icon.png',            # 程序图标
    '--add-data=data;data',           # 包含数据文件
    '--clean',                         # 清理临时文件
    '--noconfirm',                     # 不确认覆盖
    '--uac-admin',                     # 请求管理员权限
    '--hidden-import=PIL._tkinter_finder',  # 隐式导入
    '--hidden-import=win32api',
    '--hidden-import=win32con',
])
