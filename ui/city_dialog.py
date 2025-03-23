from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QPushButton, 
                            QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
                            QMessageBox, QMenu, QAction, QLabel)
from PyQt5.QtCore import Qt

class CityDialog(QDialog):
    def __init__(self, parent=None, existing_cities=None):
        super().__init__(parent)
        
        self.setWindowTitle("城市管理")
        self.setMinimumWidth(300)
        
        self.existing_cities = existing_cities or []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 添加城市的表单
        form_layout = QFormLayout()
        
        # 城市名称
        self.city_edit = QLineEdit()
        form_layout.addRow("城市名称:", self.city_edit)
        
        # 添加按钮
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_city)
        form_layout.addRow("", add_btn)
        
        layout.addLayout(form_layout)
        
        # 已添加的城市列表
        layout.addWidget(QLabel("已添加的城市:"))
        
        self.city_list = QListWidget()
        self.city_list.setSelectionMode(QListWidget.SingleSelection)
        
        # 添加现有城市
        for city in self.existing_cities:
            if city and city != "全部":
                self.city_list.addItem(city)
        
        # 设置右键菜单
        self.city_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.city_list.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.city_list)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def add_city(self):
        """添加新城市"""
        city_name = self.city_edit.text().strip()
        
        if not city_name:
            QMessageBox.warning(self, "错误", "请输入城市名称")
            return
        
        # 检查是否已存在
        for i in range(self.city_list.count()):
            if self.city_list.item(i).text() == city_name:
                QMessageBox.information(self, "提示", f"城市 '{city_name}' 已在列表中")
                return
        
        # 添加到列表
        self.city_list.addItem(city_name)
        
        # 清空输入框
        self.city_edit.clear()
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.city_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        
        # 删除操作
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.remove_city(item))
        menu.addAction(delete_action)
        
        menu.exec_(self.city_list.mapToGlobal(pos))
    
    def remove_city(self, item):
        """删除城市"""
        row = self.city_list.row(item)
        self.city_list.takeItem(row)
    
    def get_cities(self):
        """获取所有城市列表"""
        cities = []
        for i in range(self.city_list.count()):
            cities.append(self.city_list.item(i).text())
        return cities 