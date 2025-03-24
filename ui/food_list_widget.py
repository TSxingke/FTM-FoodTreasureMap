from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                            QLabel, QHBoxLayout, QComboBox, QLineEdit, QMenu,
                            QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

class FoodListWidget(QWidget):
    # 自定义信号：当选择美食项时发出
    food_selected = pyqtSignal(dict)
    food_edit_requested = pyqtSignal(int)
    food_delete_requested = pyqtSignal(int)
    foodItemDoubleClicked = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        self.food_items = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 筛选控件
        filter_layout = QVBoxLayout()
        
        # 城市筛选 - 改为可编辑的下拉框
        city_layout = QHBoxLayout()
        city_layout.addWidget(QLabel("城市:"))
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)  # 允许用户输入自定义城市
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
        
        # 设置右键菜单
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        # 为列表小部件添加双击事件
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
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
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
            
        # 获取美食数据
        food_item = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        # 查看操作
        view_action = QAction("查看详情", self)
        view_action.triggered.connect(lambda: self.food_selected.emit(food_item))
        menu.addAction(view_action)
        
        # 编辑操作
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(lambda: self.food_edit_requested.emit(food_item["id"]))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        # 删除操作
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.food_delete_requested.emit(food_item["id"]))
        menu.addAction(delete_action)
        
        menu.exec_(self.list_widget.mapToGlobal(pos))
    
    # 在第一次使用时加载所有城市列表
    def load_all_cities(self):
        """加载数据库中所有城市"""
        from data.food_manager import FoodManager
        food_manager = FoodManager()
        
        try:
            conn = food_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT city FROM food_items ORDER BY city")
            cities = [row[0] for row in cursor.fetchall()]
            
            # 清除现有项，保留"全部"选项
            while self.city_combo.count() > 1:
                self.city_combo.removeItem(1)
                
            # 添加城市
            for city in cities:
                if city and city != "全部":
                    self.city_combo.addItem(city)
        
        except Exception as e:
            print(f"加载城市列表失败: {e}")
        
        finally:
            if conn:
                conn.close()
    
    # 添加双击事件处理函数
    def on_item_double_clicked(self, item):
        # 获取点击项对应的美食数据
        food_item = item.data(Qt.UserRole)
        if food_item:
            # 发出信号，传递美食项数据
            self.foodItemDoubleClicked.emit(food_item) 