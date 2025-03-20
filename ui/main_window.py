from PyQt5.QtWidgets import (QMainWindow, QSplitter, QAction, QFileDialog, 
                            QMessageBox, QVBoxLayout, QWidget, QActionGroup)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import json
import datetime

from ui.food_list_widget import FoodListWidget
from ui.map_widget import MapWidget
from ui.food_detail_widget import FoodDetailWidget
from ui.add_food_dialog import AddFoodDialog
from data.food_manager import FoodManager
from config.api_keys import PLACE_SEARCH_AK

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
        
        # 连接详情页面的删除和编辑信号
        self.detail_widget.delete_requested.connect(self.delete_food_item)
        self.detail_widget.edit_requested.connect(self.edit_food_item)
    
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
        
        # 导入数据
        import_action = QAction("导入数据", self)
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
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
        dialog = AddFoodDialog(self, api_key=PLACE_SEARCH_AK)
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
        """导出美食数据到JSON文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            from data.food_manager import FoodManager
            manager = FoodManager()
            food_items = manager.get_all_food_items()
            
            # 为导出数据添加元数据
            export_data = {
                "metadata": {
                    "user": "当前用户",  # 可以从配置或用户信息中获取
                    "export_time": datetime.datetime.now().isoformat(),
                    "version": "1.0"
                },
                "food_items": food_items,
                "is_imported": False  # 标记为非导入数据
            }
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                success = True
            except Exception as e:
                print(f"导出数据时发生错误: {e}")
                success = False
            
            if success:
                QMessageBox.information(self, "成功", f"数据已成功导出到 {file_path}")
            else:
                QMessageBox.warning(self, "错误", "导出数据失败，请重试。")

    def import_data(self):
        """导入美食数据从JSON文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入数据", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                # 检查数据格式
                if not isinstance(import_data, dict) or "food_items" not in import_data:
                    # 尝试兼容旧格式
                    if isinstance(import_data, list):
                        food_items = import_data
                        metadata = {"user": "未知用户", "import_time": datetime.datetime.now().isoformat()}
                    else:
                        raise ValueError("不支持的数据格式")
                else:
                    food_items = import_data["food_items"]
                    metadata = import_data.get("metadata", {})
                
                # 标记为导入数据
                for item in food_items:
                    item["is_imported"] = True
                    item["imported_from"] = metadata.get("user", "未知用户")
                    item["import_time"] = datetime.datetime.now().isoformat()
                
                # 添加到数据管理器
                from data.food_manager import FoodManager
                manager = FoodManager()
                added_count = 0
                for item in food_items:
                    if manager.add_food_item(item):
                        added_count += 1
                
                # 刷新显示 - 使用正确的刷新方法
                self.load_food_data()  # 使用现有的数据加载方法
                
                QMessageBox.information(self, "导入成功", f"成功导入 {added_count} 个美食点")
                
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"导入数据时发生错误: {str(e)}") 

    def delete_food_item(self, food_id):
        """删除美食项"""
        confirm = QMessageBox.question(
            self, 
            "确认删除", 
            "确定要删除这个美食记录吗？这个操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            success = self.food_manager.delete_food_item(food_id)
            if success:
                # 刷新数据
                self.load_food_data()
                self.detail_widget.clear_details()
                QMessageBox.information(self, "成功", "美食记录已删除！")
            else:
                QMessageBox.warning(self, "错误", "删除美食记录失败，请重试。")

    def edit_food_item(self, food_id):
        """编辑美食项"""
        # 获取美食数据
        food_item = self.food_manager.get_food_item(food_id)
        if not food_item:
            QMessageBox.warning(self, "错误", "无法获取美食记录信息，请重试。")
            return
        
        # 创建编辑对话框，传入API密钥
        api_key = getattr(self.map_widget, 'api_key', None)
        if not api_key:
            # 如果地图组件没有API密钥属性，使用配置文件或者硬编码的默认值
            api_key = "IwROZMfGJmOcfruwdxtDtEAPFtyQPJp3"  # 替换为你的密钥
        
        dialog = AddFoodDialog(self, editing=True, food_data=food_item, api_key=api_key)
        
        if dialog.exec_():
            # 获取编辑后的美食数据
            updated_food = dialog.get_food_data()
            
            # 更新数据库
            success = self.food_manager.update_food_item(food_id, updated_food)
            
            if success:
                # 刷新数据
                self.load_food_data()
                QMessageBox.information(self, "成功", "美食记录已更新！")
            else:
                QMessageBox.warning(self, "错误", "更新美食记录失败，请重试。") 