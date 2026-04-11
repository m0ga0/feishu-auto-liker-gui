import os
import subprocess
import sys
import shutil


def main():
    print("🔨 开始准备打包环境...")

    # 1. 确保安装了所有必要依赖
    print("📦 正在安装依赖...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. 清理旧产物
    print("🧹 清理旧产物...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # 3. 执行标准打包命令
    # PyInstaller 会自动扫描当前环境中已安装的 customtkinter
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "飞书自动点赞助手",
        "--onefile",
        "--windowed",
        "--add-data",
        "config.example.yaml:.",
        "main.py",
    ]

    print(f"🚀 开始打包: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("✅ 打包完成！请查看 dist/ 文件夹。")


if __name__ == "__main__":
    main()
