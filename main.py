import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from ui.api_key_dialog import ApiKeyDialog
from data.database import initialize_database
from config.api_keys import PLACE_SEARCH_AK, MAP_DISPLAY_AK

def main():
    # 确保数据目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("icons", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # 初始化数据库
    initialize_database()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("美食地图")
    
    # 检查是否已配置API密钥
    if not PLACE_SEARCH_AK or not MAP_DISPLAY_AK:
        # 显示配置对话框
        dialog = ApiKeyDialog()
        dialog.setWindowTitle("首次使用 - 设置API密钥")
        if dialog.exec_():
            # 通知用户重启应用
            QMessageBox.information(None, "配置完成", "API密钥已配置，请重启应用程序。")
            return 0
        else:
            # 用户取消，退出应用
            QMessageBox.warning(None, "未配置API密钥", "需要配置API密钥才能使用应用，程序将退出。")
            return 1
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main()) 