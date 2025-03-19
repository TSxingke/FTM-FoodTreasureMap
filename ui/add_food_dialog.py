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
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.api_key = "IwROZMfGJmOcfruwdxtDtEAPFtyQPJp3"
        self.photo_paths = []
        self.location_data = None
        
        self.setWindowTitle("添加美食记录")
        self.setMinimumWidth(500)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 店铺名称
        self.name_edit = QLineEdit()
        form_layout.addRow("店铺名称:", self.name_edit)
        
        # 所在城市
        self.city_combo = QComboBox()
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州"])
        form_layout.addRow("所在城市:", self.city_combo)
        
        # 评价等级
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(1, 10)
        self.rating_spin.setValue(8)
        form_layout.addRow("评价等级:", self.rating_spin)
        
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
        
        # 位置查询区域
        location_layout = QHBoxLayout()
        self.location_label = QLabel("位置: 尚未查询")
        location_layout.addWidget(self.location_label)
        
        self.query_location_btn = QPushButton("查询位置")
        self.query_location_btn.clicked.connect(self.query_location)
        location_layout.addWidget(self.query_location_btn)
        
        layout.addLayout(location_layout)
        
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
    
    def add_photo(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择照片", "", "图片文件 (*.jpg *.jpeg *.png)"
        )
        
        if file_paths:
            self.photo_paths.extend(file_paths)
            self.update_photo_preview()
    
    def clear_photos(self):
        self.photo_paths = []
        self.photo_preview.setText("尚未上传照片")
        self.photo_preview.setPixmap(QPixmap())
    
    def update_photo_preview(self):
        if not self.photo_paths:
            return
            
        # 显示第一张照片的预览
        pixmap = QPixmap(self.photo_paths[0])
        pixmap = pixmap.scaled(QSize(300, 150), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.photo_preview.setPixmap(pixmap)
        
        # 显示照片数量
        if len(self.photo_paths) > 1:
            self.photo_preview.setText(f"已上传 {len(self.photo_paths)} 张照片")
    
    def query_location(self):
        shop_name = self.name_edit.text().strip()
        city = self.city_combo.currentText()
        
        if not shop_name:
            QMessageBox.warning(self, "错误", "请输入店铺名称")
            return
        
        try:
            # 调用百度地图API查询位置
            url = "https://api.map.baidu.com/place/v2/search"
            params = {
                "query": shop_name,
                "region": city,
                "output": "json",
                "ak": self.api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data["status"] == 0 and data["results"]:
                # 获取第一个结果
                result = data["results"][0]
                location = result["location"]
                address = result.get("address", "未知地址")
                
                self.location_data = {
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "address": address
                }
                
                self.location_label.setText(f"位置: {address} ({location['lat']}, {location['lng']})")
                self.save_btn.setEnabled(True)
            else:
                QMessageBox.warning(self, "未找到", f"未找到店铺 '{shop_name}' 的位置信息，请检查名称或手动输入位置")
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查询位置时出错: {str(e)}")
    
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
            "address": self.location_data["address"]
        } 