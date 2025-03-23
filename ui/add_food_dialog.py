from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox, 
                            QSpinBox, QTextEdit, QPushButton, QHBoxLayout, 
                            QVBoxLayout, QLabel, QFileDialog, QMessageBox, QDoubleSpinBox, QScrollArea, QMenu, QAction, QWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
import requests
import json
import os
from PIL import Image
from io import BytesIO
from data.food_manager import FoodManager

class AddFoodDialog(QDialog):
    def __init__(self, parent=None, editing=False, food_data=None, food_id=None, api_key=None):
        super().__init__(parent)
        
        self.editing = editing
        self.food_data = food_data
        self.food_id = food_id
        self.api_key = api_key
        
        # 添加这一行，初始化 food_manager
        self.food_manager = FoodManager()
        
        self.photo_paths = []
        self.existing_photos = []
        self.photos_to_delete = []
        self.location_data = {"latitude": 0, "longitude": 0, "address": ""}
        
        if editing:
            self.setWindowTitle("编辑美食")
        else:
            self.setWindowTitle("添加美食")
        
        self.setMinimumWidth(500)
        
        self.setup_ui()
        
        # 如果是编辑模式，填充现有数据
        if editing and food_data:
            self.populate_data(food_data)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 店铺名称和查询按钮
        name_layout = QHBoxLayout()
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        
        self.search_btn = QPushButton("查找")
        self.search_btn.clicked.connect(self.query_location)
        name_layout.addWidget(self.search_btn)
        
        form_layout.addRow("店铺名称:", name_layout)
        
        # 所在城市 - 改为可编辑的下拉框
        city_layout = QHBoxLayout()
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)  # 允许用户输入自定义城市
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州"])
        city_layout.addWidget(self.city_combo)
        
        form_layout.addRow("所在城市:", city_layout)
        
        # 美食类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(["中餐", "西餐", "日料", "韩餐", "火锅", "烧烤", "小吃", "甜品", "饮品", "其他"])
        form_layout.addRow("美食类型:", self.type_combo)
        
        # 评价等级 - 改用双精度微调框
        self.rating_spin = QDoubleSpinBox()
        self.rating_spin.setRange(1.0, 10.0)
        self.rating_spin.setSingleStep(0.5)  # 每次增减0.5
        self.rating_spin.setDecimals(1)  # 只显示小数点后一位
        self.rating_spin.setValue(8.0)
        form_layout.addRow("评价等级:", self.rating_spin)
        
        # 位置信息
        self.location_label = QLabel("位置: 尚未查询")
        form_layout.addRow("地址信息:", self.location_label)
        
        # 推荐理由
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("请输入推荐理由...")
        form_layout.addRow("推荐理由:", self.reason_edit)
        
        layout.addLayout(form_layout)
        
        # 照片上传区域
        photo_layout = QVBoxLayout()
        photo_layout.addWidget(QLabel("美食照片:"))
        
        # 照片预览区 - 改为滚动区域
        self.photos_scroll = QScrollArea()
        self.photos_scroll.setWidgetResizable(True)
        self.photos_scroll.setMinimumHeight(150)
        
        self.photos_container = QWidget()
        self.photos_layout = QHBoxLayout(self.photos_container)
        self.photos_scroll.setWidget(self.photos_container)
        
        photo_layout.addWidget(self.photos_scroll)
        
        # 照片操作按钮
        photo_btn_layout = QHBoxLayout()
        self.add_photo_btn = QPushButton("添加照片")
        self.add_photo_btn.clicked.connect(self.add_photo)
        photo_btn_layout.addWidget(self.add_photo_btn)
        
        self.clear_photos_btn = QPushButton("清除所有照片")
        self.clear_photos_btn.clicked.connect(self.clear_photos)
        photo_btn_layout.addWidget(self.clear_photos_btn)
        
        photo_layout.addLayout(photo_btn_layout)
        layout.addLayout(photo_layout)
        
        # 对话框按钮
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setEnabled(False)  # 初始禁用，需要先查询位置
        self.save_btn.clicked.connect(self.save_food)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def populate_data(self, food_data):
        """用现有数据填充对话框"""
        # 设置基本信息
        self.name_edit.setText(food_data.get("name", ""))
        
        # 设置城市
        city_index = self.city_combo.findText(food_data.get("city", ""))
        if city_index >= 0:
            self.city_combo.setCurrentIndex(city_index)
        
        # 设置美食类型
        type_index = self.type_combo.findText(food_data.get("food_type", "其他"))
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
        
        # 设置评分
        self.rating_spin.setValue(food_data.get("rating", 5))
        
        # 设置地址和位置信息
        address = food_data.get("address", "未知地址")
        latitude = food_data.get("latitude", 0)
        longitude = food_data.get("longitude", 0)
        
        # 存储位置数据
        self.location_data = {
            "latitude": latitude,
            "longitude": longitude,
            "address": address
        }
        
        # 更新位置标签
        self.location_label.setText(f"位置: {address} ({latitude}, {longitude})")
        
        # 设置推荐理由
        self.reason_edit.setPlainText(food_data.get("reason", ""))
        
        # 启用保存按钮，因为已经有位置信息
        self.save_btn.setEnabled(True)
        
        # 加载照片
        self.photo_paths = []
        self.existing_photos = []
        self.photos_to_delete = []
        
        # 获取照片数据
        try:
            conn = self.food_manager.get_connection()
            cursor = conn.cursor()
            
            # 查询所有相关照片
            cursor.execute("SELECT id, photo_data FROM photos WHERE food_item_id = ?", (food_data["id"],))
            photos = cursor.fetchall()
            
            if photos:
                import tempfile
                import os
                
                # 创建临时文件夹存放照片
                self.temp_dir = tempfile.mkdtemp()
                
                for i, (photo_id, photo_data) in enumerate(photos):
                    # 保存照片ID以跟踪现有照片
                    self.existing_photos.append(photo_id)
                    
                    # 将照片数据保存到临时文件
                    photo_path = os.path.join(self.temp_dir, f"photo_{i}.jpg")
                    with open(photo_path, "wb") as f:
                        f.write(photo_data)
                    
                    # 添加到照片路径列表
                    self.photo_paths.append(photo_path)
                
                # 更新照片预览
                self.update_photo_preview()
        
        except Exception as e:
            print(f"加载照片错误: {e}")
        
        finally:
            if conn:
                conn.close()
    
    def add_photo(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择照片", "", "图片文件 (*.jpg *.jpeg *.png)"
        )
        
        if file_paths:
            self.photo_paths.extend(file_paths)
            self.update_photo_preview()
    
    def clear_photos(self):
        """清除所有照片"""
        # 将所有现有照片添加到待删除列表
        self.photos_to_delete.extend(self.existing_photos)
        
        # 清空照片列表
        self.existing_photos = []
        self.photo_paths = []
        
        self.update_photo_preview()
    
    def update_photo_preview(self):
        """更新照片预览"""
        # 清除现有照片
        while self.photos_layout.count():
            item = self.photos_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.photo_paths:
            # 显示提示信息
            label = QLabel("尚未上传照片")
            label.setAlignment(Qt.AlignCenter)
            self.photos_layout.addWidget(label)
            return
        
        # 显示每张照片的预览
        for i, path in enumerate(self.photo_paths):
            photo_widget = QWidget()
            photo_layout = QVBoxLayout(photo_widget)
            photo_layout.setContentsMargins(5, 5, 5, 5)
            
            # 照片预览
            pixmap = QPixmap(path)
            pixmap = pixmap.scaled(QSize(120, 90), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            photo_label = QLabel()
            photo_label.setPixmap(pixmap)
            photo_label.setAlignment(Qt.AlignCenter)
            photo_label.setStyleSheet("border: 1px solid #ccc;")
            photo_label.setContextMenuPolicy(Qt.CustomContextMenu)
            photo_label.customContextMenuRequested.connect(lambda pos, idx=i: self.show_photo_context_menu(pos, idx))
            
            photo_layout.addWidget(photo_label)
            
            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(80, 25)
            delete_btn.clicked.connect(lambda _, idx=i: self.remove_photo(idx))
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.addWidget(delete_btn)
            
            photo_layout.addWidget(btn_container)
            
            self.photos_layout.addWidget(photo_widget)
        
        # 添加弹性空间
        self.photos_layout.addStretch()
    
    def show_photo_context_menu(self, pos, index):
        """显示照片右键菜单"""
        menu = QMenu(self)
        
        # 删除操作
        delete_action = QAction("删除此照片", self)
        delete_action.triggered.connect(lambda: self.remove_photo(index))
        menu.addAction(delete_action)
        
        # 查看操作
        view_action = QAction("查看大图", self)
        view_action.triggered.connect(lambda: self.view_photo(index))
        menu.addAction(view_action)
        
        # 显示菜单
        sender = self.sender()
        menu.exec_(sender.mapToGlobal(pos))
    
    def remove_photo(self, index):
        """删除指定索引的照片"""
        if 0 <= index < len(self.photo_paths):
            # 检查是否是现有照片（已在数据库中）
            if index < len(self.existing_photos):
                # 将照片ID添加到待删除列表
                self.photos_to_delete.append(self.existing_photos[index])
                # 从现有照片列表中移除
                self.existing_photos.pop(index)
            
            # 从路径列表中移除
            del self.photo_paths[index]
            self.update_photo_preview()
    
    def view_photo(self, index):
        """查看大图"""
        if 0 <= index < len(self.photo_paths):
            # 创建查看对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("照片预览")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # 加载图片
            pixmap = QPixmap(self.photo_paths[index])
            
            # 缩放到对话框大小，保持比例
            scaled_pixmap = pixmap.scaled(
                QSize(580, 380), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # 显示图片
            label = QLabel()
            label.setPixmap(scaled_pixmap)
            label.setAlignment(Qt.AlignCenter)
            
            layout.addWidget(label)
            
            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(close_btn)
            btn_layout.addStretch()
            
            layout.addLayout(btn_layout)
            
            dialog.exec_()
    
    def query_location(self):
        shop_name = self.name_edit.text().strip()
        city = self.city_combo.currentText()
        
        if not shop_name:
            QMessageBox.warning(self, "错误", "请输入店铺名称")
            return
        
        try:
            # 使用地点输入提示API查询位置
            url = "https://api.map.baidu.com/place/v2/suggestion"
            params = {
                "query": shop_name,
                "region": city,
                "city_limit": "true",  # 限制在当前城市内搜索
                "output": "json",
                "ak": self.api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == 0:
                results = data["result"]
                
                if not results:
                    QMessageBox.information(self, "提示", "没有找到匹配的地点")
                    return
                
                if len(results) == 1:
                    # 只有一个结果，直接使用
                    place = results[0]
                    self.use_selected_place_from_suggestion(place)
                else:
                    # 多个结果，显示选择对话框
                    from ui.place_select_dialog import PlaceSelectDialog
                    dialog = PlaceSelectDialog(results[:6], self, is_suggestion=True)  # 最多显示6个结果
                    if dialog.exec_():
                        selected_place = dialog.get_selected_place()
                        if selected_place:
                            self.use_selected_place_from_suggestion(selected_place)
            else:
                QMessageBox.warning(self, "错误", f"搜索地点失败: {data.get('message', '未知错误')}")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询位置时出错: {str(e)}")
    
    def use_selected_place_from_suggestion(self, place):
        """从地点输入提示API中使用选择的地点填充表单"""
        # 提取位置信息
        location = place.get("location", {})
        address = place.get("address", "")
        
        # 完整地址可能需要组合省市区
        if not address:
            province = place.get("province", "")
            city = place.get("city", "")
            district = place.get("district", "")
            business = place.get("business", "")
            
            address_parts = []
            if province:
                address_parts.append(province)
            if city and city != province:
                address_parts.append(city)
            if district:
                address_parts.append(district)
            if business:
                address_parts.append(business)
            
            address = "-".join(address_parts) if address_parts else "未知地址"
        
        name = place.get("name", "")
        
        # 如果名称为空，使用当前输入的名称
        if not name:
            name = self.name_edit.text().strip()
        else:
            # 更新名称输入框
            self.name_edit.setText(name)
        
        # 存储位置数据
        self.location_data = {
            "latitude": location.get("lat", 0),
            "longitude": location.get("lng", 0),
            "address": address
        }
        
        # 更新位置标签
        self.location_label.setText(
            f"位置: {address} ({self.location_data['latitude']}, {self.location_data['longitude']})"
        )
        
        # 启用保存按钮
        self.save_btn.setEnabled(True)
    
    def save_food(self):
        """保存美食记录"""
        # 验证输入
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "错误", "请输入店铺名称")
            return
        
        if not self.location_data["address"]:
            QMessageBox.warning(self, "错误", "请使用查找功能获取位置信息")
            return
        
        try:
            # 构建食品数据
            food_data = {
                "name": self.name_edit.text(),
                "city": self.city_combo.currentText(),
                "address": self.location_data["address"],
                "latitude": self.location_data["latitude"],
                "longitude": self.location_data["longitude"],
                "rating": self.rating_spin.value(),
                "reason": self.reason_edit.toPlainText(),
                "food_type": self.type_combo.currentText(),
                "collection_id": self.parent().current_collection_id if hasattr(self.parent(), 'current_collection_id') else None
            }
            
            # 明确区分编辑模式和新增模式
            if self.editing and self.food_id:
                # 编辑现有食品记录
                print(f"更新美食记录，ID: {self.food_id}")
                self.food_manager.update_food_item(self.food_id, food_data)
                food_id = self.food_id
                
                # 删除标记为删除的照片
                for photo_id in self.photos_to_delete:
                    print(f"删除照片，ID: {photo_id}")
                    self.food_manager.delete_photo(photo_id)
            else:
                # 添加新的食品记录
                print("添加新的美食记录")
                food_id = self.food_manager.add_food_item(food_data)
                print(f"新增美食记录，ID: {food_id}")
            
            # 处理照片
            for i, photo_path in enumerate(self.photo_paths):
                # 检查这个索引是否超过了现有照片数量，表示这是新添加的照片
                if i >= len(self.existing_photos):
                    try:
                        with open(photo_path, "rb") as f:
                            photo_data = f.read()
                        print(f"添加新照片到美食记录 {food_id}")
                        self.food_manager.add_photo(food_id, photo_data)
                    except Exception as e:
                        print(f"保存照片错误: {e}")
            
            QMessageBox.information(self, "成功", "美食记录已保存！")
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存美食记录失败: {str(e)}")
    
    def get_food_data(self):
        # 处理照片
        photo_data = []
        for path in self.photo_paths:
            # 读取图片并转换为合适的格式
            img = Image.open(path)
            img = img.convert('RGB')
            
            # 调整大小
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)
            
            # 保存到内存
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            photo_data.append(buffer.getvalue())
        
        # 构建美食数据
        return {
            "name": self.name_edit.text().strip(),
            "city": self.city_combo.currentText(),
            "rating": self.rating_spin.value(),
            "reason": self.reason_edit.toPlainText(),
            "photos": photo_data,
            "latitude": self.location_data["latitude"],
            "longitude": self.location_data["longitude"],
            "address": self.location_data["address"],
            "food_type": self.type_combo.currentText()
        } 