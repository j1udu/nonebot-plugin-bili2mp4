#!/usr/bin/env python3
"""
插件发布脚本
用于构建和发布nonebot-plugin-bili2mp4到PyPI
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command: str, capture_output: bool = False) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"运行命令: {command}")
    result = subprocess.run(
        command,
        shell=True,
        capture_output=capture_output,
        text=True
    )

    if result.returncode != 0:
        print(f"命令执行失败: {command}")
        if result.stdout:
            print(f"标准输出: {result.stdout}")
        if result.stderr:
            print(f"错误输出: {result.stderr}")
        sys.exit(1)

    return result

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    dirs_to_clean = ["build", "dist", "nonebot_plugin_bili2mp4.egg-info"]

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"删除目录: {dir_name}")
            shutil.rmtree(dir_name)

def build():
    """构建包"""
    print("构建包...")
    run_command("python -m build")

def test_install():
    """测试安装包"""
    print("测试安装包...")
    run_command("pip install dist/*.whl")

def uninstall():
    """卸载测试包"""
    print("卸载测试包...")
    run_command("pip uninstall -y nonebot-plugin-bili2mp4")

def publish_to_test():
    """发布到测试PyPI"""
    print("发布到测试PyPI...")
    run_command("twine upload --repository testpypi dist/*")

def publish_to_prod():
    """发布到正式PyPI"""
    print("发布到正式PyPI...")
    run_command("twine upload dist/*")

def main():
    """主函数"""
    print("NoneBot插件发布脚本")
    print("=" * 50)

    # 检查当前目录
    if not os.path.exists("pyproject.toml"):
        print("错误: 未找到pyproject.toml文件，请确保在插件根目录运行此脚本")
        sys.exit(1)

    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print("用法: python publish.py [命令]")
        print("可用命令:")
        print("  clean     - 清理构建目录")
        print("  build     - 构建包")
        print("  test      - 测试安装包")
        print("  uninstall - 卸载测试包")
        print("  test-pypi - 发布到测试PyPI")
        print("  pypi      - 发布到正式PyPI")
        print("  all       - 执行完整的构建和发布流程")
        print("  help      - 显示此帮助信息")
        return

    command = sys.argv[1]

    if command == "clean":
        clean_build()
    elif command == "build":
        clean_build()
        build()
    elif command == "test":
        test_install()
    elif command == "uninstall":
        uninstall()
    elif command == "test-pypi":
        publish_to_test()
    elif command == "pypi":
        publish_to_prod()
    elif command == "all":
        clean_build()
        build()
        print("\n构建完成！")
        print("现在可以运行以下命令发布:")
        print("  python publish.py test-pypi  # 发布到测试PyPI")
        print("  python publish.py pypi       # 发布到正式PyPI")
    else:
        print(f"未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 插件发布指南

现在你的插件已经准备就绪，可以按照以下步骤发布：

### 1. 准备GitHub仓库

1. 创建一个新的GitHub仓库：`nonebot-plugin-bili2mp4`
2. 将代码推送到GitHub：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/shengwang52005/nonebot-plugin-bili2mp4.git
git push -u origin main
```

### 2. 发布到PyPI

1. 确保你已经安装了构建和发布工具：
```bash
pip install build twine
```

2. 使用提供的发布脚本构建包：
```bash
python publish.py build
```

3. 发布到测试PyPI（推荐先测试）：
```bash
python publish.py test-pypi
```

4. 如果测试成功，发布到正式PyPI：
```bash
python publish.py pypi
```

### 3. 提交到NoneBot商店

1. 访问 [NoneBot插件商店](https://github.com/nonebot/nonebot2/tree/master/packages)
2. Fork仓库
3. 创建新文件 `packages/nonebot-plugin-bili2mp4.yml`，内容如下：

```yaml
name: nonebot-plugin-bili2mp4
desc: 在指定群内自动将B站小程序/分享链接解析并下载为MP4后发送
author: shengwang52005
homepage: https://github.com/shengwang52005/nonebot_plugin_bili2mp4
repo: https://github.com/shengwang52005/nonebot_plugin_bili2mp4
```

4. 提交Pull Request

### 注意事项

1. **版本管理**：每次更新时记得更新`pyproject.toml`中的版本号
2. **依赖管理**：确保所有依赖都已正确声明
3. **测试**：发布前在本地测试插件功能
4. **文档**：保持README.md的更新
5. **错误处理**：确保异常情况有友好的错误提示

你的插件现在已经完全符合NoneBot的发布规范，可以按照上述流程发布了！
