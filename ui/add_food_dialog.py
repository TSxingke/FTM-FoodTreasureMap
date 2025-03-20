from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox, 
                            QSpinBox, QTextEdit, QPushButton, QHBoxLayout, 
                            QVBoxLayout, QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
import requests
import json
import os
from PIL import Image
from io import BytesIO

class AddFoodDialog(QDialog):
    def __init__(self, parent=None, editing=False, food_data=None, api_key=None):
        super().__init__(parent)
        
        self.editing = editing
        self.food_data = food_data
        self.api_key = api_key or "IwROZMfGJmOcfruwdxtDtEAPFtyQPJp3"  # 使用检索专用的AK
        
        self.photos = []
        self.location_data = {"latitude": 0, "longitude": 0, "address": ""}
        
        if editing and food_data:
            self.setWindowTitle("编辑美食记录")
        else:
            self.setWindowTitle("添加美食记录")
        
        self.setup_ui()
        
        # 如果是编辑模式，填充已有数据
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
        
        # 所在城市
        self.city_combo = QComboBox()
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州"])
        form_layout.addRow("所在城市:", self.city_combo)
        
        # 评价等级
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(1, 10)
        self.rating_spin.setValue(8)
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
        
        # 照片预览区
        self.photo_preview = QLabel("尚未上传照片")
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setMinimumHeight(150)
        self.photo_preview.setStyleSheet("border: 1px dashed #ccc;")
        photo_layout.addWidget(self.photo_preview)
        
        # 照片操作按钮
        photo_btn_layout = QHBoxLayout()
        self.add_photo_btn = QPushButton("添加照片")
        self.add_photo_btn.clicked.connect(self.add_photo)
        photo_btn_layout.addWidget(self.add_photo_btn)
        
        self.clear_photos_btn = QPushButton("清除照片")
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
        self.save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def populate_data(self, food_data):
        """填充现有的美食数据"""
        # 设置基本信息
        self.name_edit.setText(food_data.get("name", ""))
        
        # 设置城市
        city_index = self.city_combo.findText(food_data.get("city", ""))
        if city_index >= 0:
            self.city_combo.setCurrentIndex(city_index)
        
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
        
        # 加载已有照片
        # 这部分暂时保留为空，因为照片数据可能比较复杂，需要单独处理
    
    def add_photo(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择照片", "", "图片文件 (*.jpg *.jpeg *.png)"
        )
        
        if file_paths:
            self.photos.extend(file_paths)
            self.update_photo_preview()
    
    def clear_photos(self):
        self.photos = []
        self.photo_preview.setText("尚未上传照片")
        self.photo_preview.setPixmap(QPixmap())
    
    def update_photo_preview(self):
        if not self.photos:
            return
            
        # 显示第一张照片的预览
        pixmap = QPixmap(self.photos[0])
        pixmap = pixmap.scaled(QSize(300, 150), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.photo_preview.setPixmap(pixmap)
        
        # 显示照片数量
        if len(self.photos) > 1:
            self.photo_preview.setText(f"已上传 {len(self.photos)} 张照片")
    
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
    
    def get_food_data(self):
        # 处理照片
        photo_data = []
        for path in self.photos:
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
            "address": self.location_data["address"]
        } 