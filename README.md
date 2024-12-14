# Windows 环境管理工具

一个用于管理 Windows 系统环境变量和系统工具的图形界面应用程序。

## 功能特点

- 环境变量管理
  - 查看/添加/修改/删除系统环境变量
  - 环境变量备份和恢复
  - PATH 变量智能管理
- 系统工具集成
  - 常用系统管理工具快速访问
  - 分类管理,便于查找
  - 工具提示说明
- 开发环境扫描
  - 自动扫描已安装的开发工具
  - 环境配置建议
  - 多版本管理支持

## 系统要求

- Windows 7/8/10/11
- Python 3.7+
- 管理员权限(部分功能需要)

## 安装说明

1. 确保已安装 Python 3.7 或更高版本
2. 安装依赖包:
   ```bash
   pip install -r requirements.txt
   ```
3. 运行程序:
   ```bash
   python -m envmanager
   ```

## 使用说明

1. 以管理员身份运行程序
2. 主界面包含三个主要功能区:
   - 环境变量管理
   - 系统工具
   - 开发环境扫描
3. 建议首次使用时进行环境备份

## 开发说明

- 项目使用 Python 标准库和少量第三方库
- 遵循 PEP 8 编码规范
- 使用 typing 进行类型提示
- 详细的日志记录

## 许可证

MIT License

## 快速开始

### 方式一：直接使用（推荐）
1. 从 [Releases](../../releases) 页面下载最新的 `EnvManager.exe`
2. 双击运行，需要管理员权限
3. 开始使用

### 方式二：从源码运行
1. 克隆仓库
   ```bash
   git clone https://github.com/你的用户名/env-manager.git
   ```
2. 进入项目目录
   ```bash
   cd env-manager
   ```
3. 运行程序
   ```bash
   python -m envmanager
   ```

6. 本地测试打包：

```bash
python build.py
```

打包完成后，可执行文件会在 `dist` 目录下。

7. 发布到 GitHub：
```bash
# 初始化 git 仓库
git init
git add .
git commit -m "Initial commit"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/env-manager.git

# 推送代码
git push -u origin main

# 创建发布标签
git tag -a v1.0.0 -m "First release"
git push origin v1.0.0
```

