from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QListWidget, QListWidgetItem, QPushButton)
from PyQt5.QtCore import Qt

class PlaceSelectDialog(QDialog):
    def __init__(self, places, parent=None, is_suggestion=False):
        super().__init__(parent)
        
        self.places = places
        self.selected_place = None
        self.is_suggestion = is_suggestion
        
        self.setWindowTitle("选择地点")
        self.resize(600, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 提示标签
        label = QLabel("找到多个匹配地点，请选择一个：")
        layout.addWidget(label)
        
        # 地点列表
        self.place_list = QListWidget()
        self.place_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.place_list)
        
        # 填充地点列表
        for place in self.places:
            if self.is_suggestion:
                # 地点输入提示API的结果格式
                address = place.get("address", "")
                if not address:
                    province = place.get("province", "")
                    city = place.get("city", "")
                    district = place.get("district", "")
                    address_parts = [p for p in [province, city, district] if p]
                    address = "-".join(address_parts) if address_parts else "未知地址"
                    
                tag = place.get("tag", "")
                item_text = f"{place['name']} ({address}) [{tag}]" if tag else f"{place['name']} ({address})"
            else:
                # 原有的地点搜索API的结果格式
                item_text = f"{place['name']} ({place['address']})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, place)
            self.place_list.addItem(item)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        select_button = QPushButton("选择")
        select_button.clicked.connect(self.accept)
        select_button.setDefault(True)
        button_layout.addWidget(select_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def accept(self):
        selected_items = self.place_list.selectedItems()
        if selected_items:
            self.selected_place = selected_items[0].data(Qt.UserRole)
            super().accept()
    
    def get_selected_place(self):
        return self.selected_place 