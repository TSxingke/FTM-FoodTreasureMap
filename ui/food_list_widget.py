from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                            QLabel, QHBoxLayout, QComboBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

class FoodListWidget(QWidget):
    # 自定义信号：当选择美食项时发出
    food_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        self.food_items = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 筛选控件
        filter_layout = QVBoxLayout()
        
        # 城市筛选
        city_layout = QHBoxLayout()
        city_layout.addWidget(QLabel("城市:"))
        self.city_combo = QComboBox()
        self.city_combo.addItem("全部")
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州"])
        self.city_combo.currentTextChanged.connect(self.apply_filters)
        city_layout.addWidget(self.city_combo)
        filter_layout.addLayout(city_layout)
        
        # 评分筛选
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("最低评分:"))
        self.rating_combo = QComboBox()
        self.rating_combo.addItems(["全部"] + [str(i) for i in range(1, 11)])
        self.rating_combo.currentTextChanged.connect(self.apply_filters)
        rating_layout.addWidget(self.rating_combo)
        filter_layout.addLayout(rating_layout)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入店铺名称...")
        self.search_edit.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_edit)
        filter_layout.addLayout(search_layout)
        
        layout.addLayout(filter_layout)
        
        # 美食列表
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.currentItemChanged.connect(self.on_item_selected)
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout)
    
    def update_food_list(self, food_items):
        """更新美食列表数据"""
        self.food_items = food_items
        self.apply_filters()
    
    def apply_filters(self):
        """应用筛选条件"""
        self.list_widget.clear()
        
        city_filter = self.city_combo.currentText()
        rating_filter = self.rating_combo.currentText()
        search_text = self.search_edit.text().lower()
        
        for item in self.food_items:
            # 应用城市筛选
            if city_filter != "全部" and item["city"] != city_filter:
                continue
            
            # 应用评分筛选
            if rating_filter != "全部" and item["rating"] < int(rating_filter):
                continue
            
            # 应用搜索筛选
            if search_text and search_text not in item["name"].lower():
                continue
            
            # 创建列表项
            list_item = QListWidgetItem()
            
            # 设置图标（根据评分）
            if item["rating"] >= 9:
                list_item.setIcon(QIcon("icons/star_gold.png"))
            elif item["rating"] >= 7:
                list_item.setIcon(QIcon("icons/star_silver.png"))
            else:
                list_item.setIcon(QIcon("icons/star_bronze.png"))
            
            # 设置文本
            list_item.setText(f"{item['name']} ({item['city']}) - {item['rating']}分")
            
            # 存储美食数据
            list_item.setData(Qt.UserRole, item)
            
            self.list_widget.addItem(list_item)
    
    def on_item_selected(self, current, previous):
        """当选择列表项时触发"""
        if current:
            # 获取美食数据
            food_item = current.data(Qt.UserRole)
            
            # 发出信号
            self.food_selected.emit(food_item) 