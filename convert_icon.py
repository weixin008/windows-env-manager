from PIL import Image
import os
from pathlib import Path

def convert_to_ico(png_path, ico_path):
    try:
        # 打印当前工作目录和文件路径，用于调试
        print(f"当前工作目录: {os.getcwd()}")
        print(f"尝试读取文件: {png_path}")
        
        # 确保输入文件存在
        if not os.path.exists(png_path):
            raise FileNotFoundError(f"PNG文件不存在: {png_path}")
            
        # 创建输出目录
        os.makedirs(os.path.dirname(ico_path), exist_ok=True)
        
        # 转换图片
        img = Image.open(png_path)
        img.save(ico_path, format='ICO')
        print(f"成功将 {png_path} 转换为 {ico_path}")
        
    except Exception as e:
        print(f"转换失败: {str(e)}")

if __name__ == "__main__":
    # 使用相对于当前脚本的路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建输入输出路径
    png_path = os.path.join(current_dir, "data", "icon.png")  # 修改为 data 文件夹下的路径
    ico_path = os.path.join(current_dir, "data", "images", "icon.ico")
    
    convert_to_ico(png_path, ico_path)
