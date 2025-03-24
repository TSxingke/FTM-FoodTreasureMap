import os
import sys
from create_icons import main as create_icons

def main():
    # 确保目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("icons", exist_ok=True)
    
    # 检查图标
    from create_icons import main as check_icons
    missing_icons = check_icons()
    if missing_icons:
        print("请添加缺失的图标后重新启动应用程序。")
    
    # 导入并运行主程序
    from main import main as run_app
    run_app()

if __name__ == "__main__":
    main() 