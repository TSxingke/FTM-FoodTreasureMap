from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QHBoxLayout, QLabel, QMessageBox)
from PyQt5.QtCore import Qt

from config.api_keys import save_config, PLACE_SEARCH_AK, MAP_DISPLAY_AK

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("设置API密钥")
        self.setMinimumWidth(400)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 说明文字
        info_label = QLabel(
            "请设置百度地图API密钥(AK)，应用将使用两个密钥："
            "<ul>"
            "<li><b>地点搜索密钥:</b> 用于查询美食地点的位置信息</li>"
            "<li><b>地图显示密钥:</b> 用于显示地图和标记</li>"
            "</ul>"
            "密钥配置一次后将自动保存，无需再次设置。"
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 地点搜索密钥
        self.place_search_edit = QLineEdit()
        self.place_search_edit.setText(PLACE_SEARCH_AK)
        self.place_search_edit.setPlaceholderText("输入地点搜索AK...")
        form_layout.addRow("地点搜索密钥:", self.place_search_edit)
        
        # 地图显示密钥
        self.map_display_edit = QLineEdit()
        self.map_display_edit.setText(MAP_DISPLAY_AK)
        self.map_display_edit.setPlaceholderText("输入地图显示AK...")
        form_layout.addRow("地图显示密钥:", self.map_display_edit)
        
        layout.addLayout(form_layout)
        
        # 帮助信息
        help_label = QLabel(
            "如何获取密钥：<br>"
            "1. 访问百度地图开放平台: <a href='https://lbsyun.baidu.com/'>https://lbsyun.baidu.com/</a><br>"
            "2. 注册并登录账号<br>"
            "3. 在控制台创建应用，获取AK<br>"
            "4. 对于地点搜索，应用类型选择'服务端'，对于地图显示，应用类型选择'浏览器端'"
        )
        help_label.setWordWrap(True)
        help_label.setTextFormat(Qt.RichText)
        help_label.setOpenExternalLinks(True)
        layout.addWidget(help_label)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_keys)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def save_keys(self):
        place_search_ak = self.place_search_edit.text().strip()
        map_display_ak = self.map_display_edit.text().strip()
        
        if not place_search_ak or not map_display_ak:
            QMessageBox.warning(self, "错误", "请输入两个API密钥")
            return
        
        # 保存配置
        if save_config(place_search_ak, map_display_ak):
            QMessageBox.information(self, "成功", "API密钥已保存，重启应用后生效")
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "保存API密钥失败") 