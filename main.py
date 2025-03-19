import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from data.database import initialize_database

def main():
    # 确保数据目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("icons", exist_ok=True)
    
    # 初始化数据库
    initialize_database()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("美食地图")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 