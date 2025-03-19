from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                            QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QBuffer
from PyQt5.QtGui import QPixmap, QImage, QFont
from data.food_manager import FoodManager
from io import BytesIO

class FoodDetailWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.food_manager = FoodManager()
        self.current_food_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 创建内容部件
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        
        # 标题
        self.title_label = QLabel("请选择一个美食点")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.content_layout.addWidget(self.title_label)
        
        # 基本信息
        self.info_layout = QGridLayout()
        self.content_layout.addLayout(self.info_layout)
        
        # 推荐理由
        self.reason_label = QLabel()
        self.reason_label.setWordWrap(True)
        self.reason_label.setTextFormat(Qt.RichText)
        self.content_layout.addWidget(self.reason_label)
        
        # 照片区域
        self.photos_layout = QHBoxLayout()
        self.content_layout.addLayout(self.photos_layout)
        
        # 设置滚动区域的部件
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
    
    def display_food_details(self, food_item):
        """显示美食详情"""
        self.current_food_id = food_item["id"]
        
        # 清除现有内容
        self.clear_layout(self.info_layout)
        self.clear_layout(self.photos_layout)
        
        # 设置标题
        self.title_label.setText(food_item["name"])
        
        # 设置基本信息
        info_items = [
            ("城市:", food_item["city"]),
            ("评分:", f"{food_item['rating']} / 10"),
            ("地址:", food_item["address"]),
            ("坐标:", f"({food_item['latitude']:.6f}, {food_item['longitude']:.6f})"),
            ("添加时间:", food_item["created_at"].split("T")[0])
        ]
        
        for row, (label, value) in enumerate(info_items):
            self.info_layout.addWidget(QLabel(label), row, 0)
            self.info_layout.addWidget(QLabel(value), row, 1)
        
        # 设置推荐理由
        reason_text = food_item.get("reason", "")
        if reason_text:
            self.reason_label.setText(f"<b>推荐理由:</b><br>{reason_text}")
            self.reason_label.show()
        else:
            self.reason_label.hide()
        
        # 加载照片
        self.load_photos(food_item["id"], food_item.get("photo_ids", []))
    
    def load_photos(self, food_id, photo_ids):
        """加载美食照片"""
        if not photo_ids:
            self.photos_layout.addWidget(QLabel("暂无照片"))
            return
        
        # 获取完整的美食数据（包含照片）
        food_data = self.food_manager.get_food_item(food_id)
        if not food_data or not food_data.get("photos"):
            self.photos_layout.addWidget(QLabel("无法加载照片"))
            return
        
        # 显示照片
        for photo in food_data["photos"]:
            # 从二进制数据创建图像
            image = QImage.fromData(photo["data"])
            pixmap = QPixmap.fromImage(image)
            
            # 调整大小
            pixmap = pixmap.scaled(QSize(200, 150), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 创建标签显示图像
            photo_label = QLabel()
            photo_label.setPixmap(pixmap)
            photo_label.setAlignment(Qt.AlignCenter)
            photo_label.setStyleSheet("border: 1px solid #ccc; margin: 5px;")
            
            self.photos_layout.addWidget(photo_label)
        
        # 添加弹性空间
        self.photos_layout.addStretch()
    
    def clear_layout(self, layout):
        """清除布局中的所有部件"""
        if layout is None:
            return
            
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout()) 