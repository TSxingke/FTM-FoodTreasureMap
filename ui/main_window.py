from PyQt5.QtWidgets import (QMainWindow, QSplitter, QAction, QFileDialog, 
                            QMessageBox, QVBoxLayout, QWidget, QActionGroup)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from ui.food_list_widget import FoodListWidget
from ui.map_widget import MapWidget
from ui.food_detail_widget import FoodDetailWidget
from ui.add_food_dialog import AddFoodDialog
from data.food_manager import FoodManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.food_manager = FoodManager()
        
        self.setWindowTitle("美食地图")
        self.setMinimumSize(1200, 800)
        
        # 创建主布局
        self.setup_ui()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 加载数据
        self.load_food_data()
    
    def setup_ui(self):
        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧美食列表
        self.food_list_widget = FoodListWidget()
        self.food_list_widget.food_selected.connect(self.on_food_selected)
        main_splitter.addWidget(self.food_list_widget)
        
        # 创建右侧分割器
        right_splitter = QSplitter(Qt.Vertical)
        
        # 创建地图显示区域
        self.map_widget = MapWidget()
        right_splitter.addWidget(self.map_widget)
        
        # 创建美食详情区域
        self.detail_widget = FoodDetailWidget()
        right_splitter.addWidget(self.detail_widget)
        
        # 设置右侧分割比例
        right_splitter.setSizes([600, 200])
        
        # 添加右侧分割器到主分割器
        main_splitter.addWidget(right_splitter)
        
        # 设置主分割器比例
        main_splitter.setSizes([300, 900])
        
        # 设置中央部件
        self.setCentralWidget(main_splitter)
    
    def create_menu_bar(self):
        # 创建菜单栏
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        # 添加美食记录
        add_action = QAction(QIcon("icons/add.png"), "添加美食", self)
        add_action.setShortcut("Ctrl+N")
        add_action.triggered.connect(self.show_add_food_dialog)
        file_menu.addAction(add_action)
        
        # 导出数据
        export_action = QAction(QIcon("icons/export.png"), "导出数据", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction(QIcon("icons/exit.png"), "退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图")
        
        # 全国视图
        country_view_action = QAction("全国视图", self)
        country_view_action.setCheckable(True)
        country_view_action.triggered.connect(lambda: self.map_widget.set_view_mode("country"))
        view_menu.addAction(country_view_action)
        
        # 城市视图
        city_view_action = QAction("城市视图", self)
        city_view_action.setCheckable(True)
        city_view_action.triggered.connect(lambda: self.map_widget.set_view_mode("city"))
        view_menu.addAction(city_view_action)
        
        # 设置默认选中
        country_view_action.setChecked(True)
        
        # 创建视图操作组
        view_group = QActionGroup(self)
        view_group.addAction(country_view_action)
        view_group.addAction(city_view_action)
        view_group.setExclusive(True)
    
    def load_food_data(self):
        # 从数据库加载美食数据
        food_items = self.food_manager.get_all_food_items()
        
        # 更新列表
        self.food_list_widget.update_food_list(food_items)
        
        # 更新地图
        self.map_widget.plot_food_locations(food_items)
    
    def show_add_food_dialog(self):
        dialog = AddFoodDialog(self)
        if dialog.exec_():
            # 获取新添加的美食数据
            food_data = dialog.get_food_data()
            
            # 保存到数据库
            food_id = self.food_manager.add_food_item(food_data)
            
            if food_id:
                # 刷新数据
                self.load_food_data()
                QMessageBox.information(self, "成功", "美食记录添加成功！")
            else:
                QMessageBox.warning(self, "错误", "添加美食记录失败，请重试。")
    
    def on_food_selected(self, food_item):
        # 更新详情显示
        self.detail_widget.display_food_details(food_item)
        
        # 在地图上高亮显示
        self.map_widget.highlight_food_location(food_item)
    
    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "", "JSON文件 (*.json);;CSV文件 (*.csv)"
        )
        
        if file_path:
            success = self.food_manager.export_data(file_path)
            if success:
                QMessageBox.information(self, "成功", f"数据已成功导出到 {file_path}")
            else:
                QMessageBox.warning(self, "错误", "导出数据失败，请重试。") 