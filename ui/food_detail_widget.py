from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                            QScrollArea, QGridLayout, QPushButton)
from PyQt5.QtCore import Qt, QSize, QBuffer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from data.food_manager import FoodManager
from io import BytesIO

class FoodDetailWidget(QWidget):
    # 添加信号
    delete_requested = pyqtSignal(int)  # 传递美食ID
    edit_requested = pyqtSignal(int)    # 传递美食ID
    
    def __init__(self):
        super().__init__()
        
        self.food_manager = FoodManager()
        self.current_food_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        
        # 标题
        self.title_label = QLabel("请选择美食项")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.title_label)
        
        # 操作按钮区域
        action_layout = QHBoxLayout()
        
        # 编辑按钮
        self.edit_button = QPushButton("编辑")
        self.edit_button.setIcon(QIcon("icons/edit.png"))
        self.edit_button.clicked.connect(self.request_edit)
        action_layout.addWidget(self.edit_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setIcon(QIcon("icons/delete.png"))
        self.delete_button.clicked.connect(self.request_delete)
        action_layout.addWidget(self.delete_button)
        
        action_layout.addStretch()
        main_layout.addLayout(action_layout)
        
        # 信息区域
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        info_widget = QWidget()
        info_scroll.setWidget(info_widget)
        
        info_layout = QVBoxLayout(info_widget)
        
        # 基本信息区
        basic_info_widget = QWidget()
        self.info_layout = QGridLayout(basic_info_widget)
        info_layout.addWidget(basic_info_widget)
        
        # 推荐理由
        self.reason_label = QLabel()
        self.reason_label.setWordWrap(True)
        info_layout.addWidget(self.reason_label)
        
        # 照片区域
        photos_widget = QWidget()
        self.photos_layout = QHBoxLayout(photos_widget)
        info_layout.addWidget(photos_widget)
        
        info_layout.addStretch()
        
        main_layout.addWidget(info_scroll)
        self.setLayout(main_layout)
        
        # 初始时禁用按钮
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
    
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
        
        # 启用按钮
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)
    
    def load_photos(self, food_id, photo_ids):
        """加载照片"""
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
        """清除布局中的所有控件"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())
    
    def request_edit(self):
        """请求编辑当前美食项"""
        if self.current_food_id is not None:
            self.edit_requested.emit(self.current_food_id)
    
    def request_delete(self):
        """请求删除当前美食项"""
        if self.current_food_id is not None:
            self.delete_requested.emit(self.current_food_id)
    
    def clear_details(self):
        """清除详情显示"""
        self.current_food_id = None
        self.title_label.setText("请选择美食项")
        self.clear_layout(self.info_layout)
        self.clear_layout(self.photos_layout)
        self.reason_label.hide()
        
        # 禁用按钮
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False) 