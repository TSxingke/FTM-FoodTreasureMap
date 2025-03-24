from PyQt5.QtWidgets import (QMainWindow, QSplitter, QAction, QFileDialog, 
                            QMessageBox, QVBoxLayout, QWidget, QActionGroup, QHBoxLayout, QComboBox, QPushButton, QInputDialog, QLabel, QDialog, QStatusBar, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
import json
import datetime
import os

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
        
        # 初始化成员变量，避免未定义错误
        self.dataset_label = None
        
        self.setWindowTitle("美食地图")
        self.setMinimumSize(1200, 800)
        
        # 设置应用图标
        app_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "FTM.png")
        if os.path.exists(app_icon_path):
            self.setWindowIcon(QIcon(app_icon_path))
            
        # 应用样式表
        self.apply_stylesheet()
        
        # 创建主布局
        self.setup_ui()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 加载数据
        self.load_food_data()
        
        # 连接食物列表的双击信号
        self.food_list_widget.foodItemDoubleClicked.connect(self.on_food_item_double_clicked)
    
    def apply_stylesheet(self):
        """应用应用程序样式表"""
        style = """
        QMainWindow {
            background-color: #f5f7fa;
        }
        
        QMenuBar {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 4px;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 6px 10px;
            margin: 0px 2px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background-color: #2980b9;
        }
        
        QMenu {
            background-color: white;
            border: 1px solid #dcdde1;
            border-radius: 4px;
            padding: 5px;
        }
        
        QMenu::item {
            padding: 6px 25px 6px 25px;
            border-radius: 3px;
        }
        
        QMenu::item:selected {
            background-color: #3498db;
            color: white;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 15px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #1c6ea4;
        }
        
        QComboBox {
            border: 1px solid #dcdde1;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #dcdde1;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }
        
        QComboBox QAbstractItemView {
            border: 1px solid #dcdde1;
            border-radius: 4px;
            background-color: white;
            selection-background-color: #3498db;
            selection-color: white;
        }
        
        QStatusBar {
            background-color: #f8f9fa;
            color: #333;
            border-top: 1px solid #dcdde1;
        }
        
        QSplitter::handle {
            background-color: #dcdde1;
        }
        
        QSplitter::handle:horizontal {
            width: 2px;
        }
        
        QSplitter::handle:vertical {
            height: 2px;
        }
        """
        self.setStyleSheet(style)
    
    def setup_ui(self):
        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        
        # 创建左侧美食列表，连接信号
        self.food_list_widget = FoodListWidget()
        self.food_list_widget.food_selected.connect(self.show_food_detail_dialog)
        self.food_list_widget.food_edit_requested.connect(self.edit_food_item)
        self.food_list_widget.food_delete_requested.connect(self.delete_food_item)
        main_splitter.addWidget(self.food_list_widget)
        
        # 直接将地图组件添加到右侧，不再使用垂直分割器
        self.map_widget = MapWidget()
        main_splitter.addWidget(self.map_widget)
        
        # 设置主分割器的初始大小
        main_splitter.setSizes([200, 600])
        
        # 将主分割器设置为中央控件
        self.setCentralWidget(main_splitter)
        
        # 添加地图集合选择器
        self.add_collection_selector()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        # 设置菜单栏样式
        menubar = self.menuBar()
        menubar.setFont(QFont("微软雅黑", 9))
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        # 导入美食数据
        import_action = QAction(QIcon("icons/import.png"), "导入数据", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_food_data)
        file_menu.addAction(import_action)
        
        # 导出美食数据
        export_action = QAction(QIcon("icons/export.png"), "导出数据", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_food_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction(QIcon("icons/exit.png"), "退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu("设置")
        
        # API密钥设置
        api_action = QAction(QIcon("icons/key.png"), "设置API密钥", self)
        api_action.triggered.connect(self.set_api_keys)
        settings_menu.addAction(api_action)
        
        # 添加工具栏
        self.create_toolbar()
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # 添加食物按钮
        add_action = QAction(QIcon("icons/add.png"), "添加美食", self)
        add_action.triggered.connect(self.show_add_food_dialog)
        toolbar.addAction(add_action)
        
        # 移除导入导出按钮，保留在菜单中
        # 添加弹性空间，将后续内容推到右侧
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        
        # 创建视图模式切换按钮
        self.create_view_mode_buttons(toolbar)
    
    def create_status_bar(self):
        """创建底部状态栏"""
        status_bar = self.statusBar()
        
        # 设置默认状态信息
        status_bar.showMessage("美食地图应用已准备就绪")
        
        # 添加数据集信息标签
        self.dataset_label = QLabel()
        status_bar.addPermanentWidget(self.dataset_label)
        
        # 初始化标签内容
        self.update_status_dataset_info()
    
    def update_status_dataset_info(self):
        """更新状态栏中的数据集信息"""
        # 检查必要的组件是否已创建
        if not hasattr(self, 'dataset_label') or self.dataset_label is None:
            return
        
        if not hasattr(self, 'food_list_widget') or self.food_list_widget is None:
            # 组件尚未创建，暂时不更新
            self.dataset_label.setText("准备中...")
            return
        
        # 尝试获取食物列表中的项目数量
        try:
            # 如果有 count 方法就直接使用
            if hasattr(self.food_list_widget, 'count') and callable(self.food_list_widget.count):
                count = self.food_list_widget.count()
            # 否则使用列表视图的计数方法
            elif hasattr(self.food_list_widget, 'listWidget') and hasattr(self.food_list_widget.listWidget, 'count'):
                count = self.food_list_widget.listWidget.count()
            # 否则检查是否有食物项列表属性
            elif hasattr(self.food_list_widget, 'food_items'):
                count = len(self.food_list_widget.food_items)
            else:
                # 无法获取数量，使用默认值
                count = 0
        except Exception as e:
            print(f"获取美食项数量时出错: {e}")
            count = 0
        
        # 更新标签文本
        collection_name = "未选择地图"
        if hasattr(self, 'current_collection_id') and self.current_collection_id and hasattr(self, 'collection_combo'):
            for i in range(self.collection_combo.count()):
                if self.collection_combo.itemData(i) == self.current_collection_id:
                    collection_name = self.collection_combo.itemText(i)
                    break
        
        self.dataset_label.setText(f"当前地图: {collection_name} | 共 {count} 条美食记录")
    
    def load_food_data(self):
        """从数据库加载美食数据，基于当前选择的集合"""
        if hasattr(self, 'current_collection_id') and self.current_collection_id:
            food_items = self.food_manager.get_food_items_by_collection(self.current_collection_id)
            
            # 更新列表
            self.food_list_widget.update_food_list(food_items)
            
            # 更新地图
            self.map_widget.plot_food_locations(food_items)
            
            # 确保应用当前的视图模式
            if hasattr(self, 'current_view_mode'):
                self.map_widget.set_view_mode(self.current_view_mode)
        
        # 在加载完数据后更新状态栏
        self.update_status_dataset_info()
        
        # 更新状态栏消息，使用statusBar()方法获取状态栏
        self.statusBar().showMessage(f"已成功加载美食数据", 3000)
    
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
    
    def show_food_detail_dialog(self, food_item):
        """弹出对话框显示美食详情"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"美食详情 - {food_item['name']}")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 创建详情组件
        detail_widget = FoodDetailWidget()
        detail_widget.set_food_data(food_item)
        
        layout.addWidget(detail_widget)
        
        # 底部关闭按钮
        button_layout = QHBoxLayout()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def export_food_data(self):
        """导出当前地图集合到JSON文件"""
        if not hasattr(self, 'current_collection_id') or not self.current_collection_id:
            QMessageBox.warning(self, "错误", "请先选择一个地图集合")
            return
        
        # 获取当前集合名称
        collection_name = "美食地图"
        for i in range(self.collection_combo.count()):
            if self.collection_combo.itemData(i) == self.current_collection_id:
                collection_name = self.collection_combo.itemText(i).split(" (")[0]  # 移除可能的"(个人)"后缀
                break
        
        # 构建默认文件名
        default_filename = f"{collection_name}_{datetime.date.today().strftime('%Y%m%d')}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出地图", default_filename, "JSON文件 (*.json)"
        )
        
        if file_path:
            success = self.food_manager.export_collection(self.current_collection_id, file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"地图已成功导出到 {file_path}")
            else:
                QMessageBox.warning(self, "错误", "导出地图失败，请重试。")

    def import_food_data(self):
        """导入地图集合从JSON文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入地图", "", "JSON文件 (*.json)"
        )
        
        if file_path:
            # 询问自定义名称
            basename = os.path.basename(file_path)
            name, ok = QInputDialog.getText(
                self, 
                "地图名称", 
                "请输入导入地图的名称:",
                text=os.path.splitext(basename)[0]
            )
            
            if ok:
                success, message = self.food_manager.import_collection(file_path, name)
                if success:
                    QMessageBox.information(self, "成功", message)
                    # 重新加载集合
                    self.load_collections()
                else:
                    QMessageBox.warning(self, "错误", message)

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
                QMessageBox.information(self, "成功", "美食记录已删除！")
            else:
                QMessageBox.warning(self, "错误", "删除美食记录失败，请重试。")

    def edit_food_item(self, food_id):
        """编辑美食记录"""
        try:
            # 获取美食数据
            food_data = self.food_manager.get_food_item(food_id)
            
            if food_data:
                # 创建编辑对话框，使用PLACE_SEARCH_AK而不是self.api_key
                dialog = AddFoodDialog(
                    self, 
                    editing=True,
                    food_data=food_data,
                    food_id=food_id,
                    api_key=PLACE_SEARCH_AK  # 改为直接使用导入的常量
                )
                
                if dialog.exec_():
                    # 更新列表和地图
                    self.load_food_data()  # 使用load_food_data替代未定义的refresh_food_list和update_map_markers方法
                    QMessageBox.information(self, "成功", "美食记录已更新！")
        
        except Exception as e:
            QMessageBox.warning(self, "错误", f"编辑美食记录时出错: {str(e)}")

    def set_api_keys(self):
        from ui.api_key_dialog import ApiKeyDialog
        dialog = ApiKeyDialog(self)
        if dialog.exec_():
            # 提示用户重启应用
            QMessageBox.information(self, "提示", "API密钥设置已保存，请重启应用以应用更改")

    def add_collection_selector(self):
        """添加地图集合选择器"""
        collections_widget = QWidget()
        collections_layout = QHBoxLayout(collections_widget)
        collections_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加标签
        collections_layout.addWidget(QLabel("当前地图:"))
        
        # 添加下拉菜单
        self.collection_combo = QComboBox()
        self.collection_combo.currentIndexChanged.connect(self.on_collection_changed)
        collections_layout.addWidget(self.collection_combo)
        
        # 添加创建按钮
        new_collection_btn = QPushButton("新建")
        new_collection_btn.clicked.connect(self.create_new_collection)
        collections_layout.addWidget(new_collection_btn)
        
        # 添加删除按钮
        delete_collection_btn = QPushButton("删除")
        delete_collection_btn.clicked.connect(self.delete_collection)
        collections_layout.addWidget(delete_collection_btn)
        
        # 添加到主工具栏
        self.toolbar = self.addToolBar("地图集合")
        self.toolbar.addWidget(collections_widget)
        
        # 加载地图集合
        self.load_collections()

    def load_collections(self):
        """加载所有地图集合到下拉菜单"""
        self.collection_combo.clear()
        
        # 获取所有地图集合
        collections = self.food_manager.get_map_collections()
        
        for collection in collections:
            # 对个人集合特殊标记
            name = collection["name"]
            if collection["is_personal"]:
                name += " (个人)"
            
            self.collection_combo.addItem(name, collection["id"])
        
        # 如果有集合，选择第一个
        if self.collection_combo.count() > 0:
            self.collection_combo.setCurrentIndex(0)
            self.current_collection_id = self.collection_combo.currentData()
        else:
            self.current_collection_id = self.food_manager.personal_collection_id

    def on_collection_changed(self, index):
        """当选择不同的地图集合时"""
        if index >= 0:
            self.current_collection_id = self.collection_combo.itemData(index)
            self.load_food_data()

    def create_new_collection(self):
        """创建新的地图集合"""
        name, ok = QInputDialog.getText(self, "新建地图", "请输入地图名称:")
        
        if ok and name:
            description, ok = QInputDialog.getText(self, "地图描述", "请输入地图描述:")
            
            if ok:
                conn = self.food_manager.get_connection()
                cursor = conn.cursor()
                
                try:
                    # 插入新集合
                    cursor.execute("""
                        INSERT INTO map_collections (name, description, is_personal, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (
                        name,
                        description or "",
                        1,  # 个人集合
                        datetime.datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    
                    # 重新加载集合列表
                    self.load_collections()
                    
                    # 选择新创建的集合
                    for i in range(self.collection_combo.count()):
                        if self.collection_combo.itemData(i) == cursor.lastrowid:
                            self.collection_combo.setCurrentIndex(i)
                            break
                    
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"创建地图失败: {str(e)}")
                
                finally:
                    conn.close()

    def delete_collection(self):
        """删除当前选中的地图集合"""
        if not hasattr(self, 'current_collection_id') or not self.current_collection_id:
            QMessageBox.warning(self, "错误", "请先选择一个地图集合")
            return
        
        # 获取当前集合信息
        for i in range(self.collection_combo.count()):
            if self.collection_combo.itemData(i) == self.current_collection_id:
                collection_name = self.collection_combo.itemText(i)
                is_personal = "(个人)" in collection_name
                break
        else:
            QMessageBox.warning(self, "错误", "无法获取地图信息")
            return
        
        # 不允许删除个人默认地图
        if is_personal and self.current_collection_id == self.food_manager.personal_collection_id:
            QMessageBox.warning(self, "错误", "不能删除默认的个人地图")
            return
        
        # 确认删除
        confirm = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除地图 '{collection_name}' 吗？\n这将删除该地图中的所有美食记录，此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                conn = self.food_manager.get_connection()
                cursor = conn.cursor()
                
                # 删除地图及其关联的所有美食项
                cursor.execute("DELETE FROM map_collections WHERE id = ?", (self.current_collection_id,))
                conn.commit()
                
                QMessageBox.information(self, "成功", f"地图 '{collection_name}' 已删除")
                
                # 重新加载集合列表
                self.load_collections()
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除地图失败: {str(e)}")
            
            finally:
                if conn:
                    conn.close()

    def on_food_item_double_clicked(self, food_item):
        """
        处理美食列表项被双击的事件
        
        Args:
            food_item: 被双击的美食数据项
        """
        # 获取美食点ID
        food_id = food_item['id']
        
        # 调用地图widget的方法显示信息窗口
        self.map_widget.show_food_info_window(food_id)
        
        # 同时高亮显示该美食点
        self.map_widget.highlight_food_location(food_item)

    def create_view_mode_buttons(self, toolbar):
        """创建视图模式切换按钮，添加到工具栏的右侧"""
        # 创建单选按钮组
        self.view_mode_group = QActionGroup(self)
        self.view_mode_group.setExclusive(True)
        
        # 创建全国视图按钮 - 不使用图标
        self.country_view_action = QAction("全国视图", self)
        self.country_view_action.setCheckable(True)
        self.country_view_action.setChecked(True)  # 默认选中全国视图
        self.country_view_action.triggered.connect(lambda: self.change_view_mode("country"))
        self.view_mode_group.addAction(self.country_view_action)
        
        # 创建城市视图按钮 - 不使用图标
        self.city_view_action = QAction("城市视图", self)
        self.city_view_action.setCheckable(True)
        self.city_view_action.triggered.connect(lambda: self.change_view_mode("city"))
        self.view_mode_group.addAction(self.city_view_action)
        
        # 添加视图模式按钮到工具栏
        toolbar.addAction(self.country_view_action)
        toolbar.addAction(self.city_view_action)
        
        # 初始化视图模式
        self.current_view_mode = "country"

    def change_view_mode(self, mode):
        """切换视图模式"""
        if mode != self.current_view_mode:
            self.current_view_mode = mode
            
            # 调用地图窗口的方法切换视图
            self.map_widget.set_view_mode(mode)
            
            # 更新状态栏信息
            status_message = "已切换到城市视图" if mode == "city" else "已切换到全国视图"
            self.statusBar().showMessage(status_message, 3000) 