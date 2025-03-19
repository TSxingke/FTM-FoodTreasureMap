import os
import sys
from create_icons import main as create_icons

def main():
    # 确保目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("icons", exist_ok=True)
    
    # 创建图标
    create_icons()
    
    # 导入并运行主程序
    from main import main as run_app
    run_app()

if __name__ == "__main__":
    main() 