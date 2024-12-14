from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="windows-env-manager",
    version="1.0.0",
    author="一个豆",
    description="Windows系统环境管理工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.7",
    ],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=9.0.0",
        "pywin32>=228",
    ],
    entry_points={
        "console_scripts": [
            "envmanager=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["data/*.json", "data/images/*"],
    },
)
