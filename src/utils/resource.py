import os
import sys
import logging
from pathlib import Path

def resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径
    
    Args:
        relative_path: 相对于项目根目录的路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹,将路径存储在_MEIPASS中
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            # 如果不是打包后的执行，就使用当前文件所在目录的上两级作为基准
            base_path = Path(__file__).parent.parent.parent
            
        full_path = os.path.join(base_path, relative_path)
        logging.debug(f"资源文件路径: {full_path}")
        return full_path
        
    except Exception as e:
        logging.error(f"获取资源文件路径失败: {str(e)}")
        return relative_path

# 定义常用资源路径
IMAGES_DIR = Path(resource_path('data/images'))