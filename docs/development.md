# 开发文档

## 项目结构
src/
├── core/ # 核心功能模块
├── gui/ # 图形界面模块
├── utils/ # 工具类模块
└── main.py # 程序入口

## 开发环境设置

1. 克隆项目并进入项目目录
2. 创建虚拟环境:

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. 安装开发依赖:
```bash
pip install -r requirements.txt
```

## 编码规范

- 遵循 PEP 8
- 使用 Black 格式化代码
- 使用 Pylint 进行代码检查
- 使用 MyPy 进行类型检查

## 测试

```bash
# 运行单元测试
pytest

# 生成覆盖率报告
pytest --cov=src tests/
```

## 构建和发布

```bash
# 构建包
python setup.py sdist bdist_wheel

# 安装开发版本
pip install -e .
```
