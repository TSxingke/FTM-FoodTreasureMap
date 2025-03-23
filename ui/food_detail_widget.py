from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                            QScrollArea, QGridLayout, QPushButton, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QBuffer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from data.food_manager import FoodManager
from io import BytesIO

class FoodDetailWidget(QWidget):
    # 添加信号
    delete_requested = pyqtSignal(int)  # 传递美食ID
    edit_requested = pyqtSignal(int)    # 传递美食ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.food_manager = FoodManager()
        self.food_data = None
        self.current_food_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        
        # 创建内容布局
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        
        # 美食名称
        self.name_label = QLabel("选择一个美食点以查看详情")
        self.name_label.setAlignment(Qt.AlignCenter)
        font = self.name_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.name_label.setFont(font)
        self.content_layout.addWidget(self.name_label)
        
        # 评分
        self.rating_label = QLabel("评分: --")
        self.rating_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.rating_label)
        
        # 城市和地址
        info_layout = QVBoxLayout()
        self.city_label = QLabel("城市: --")
        self.address_label = QLabel("地址: --")
        self.type_label = QLabel("类型: --")
        
        info_layout.addWidget(self.city_label)
        info_layout.addWidget(self.address_label)
        info_layout.addWidget(self.type_label)
        
        self.content_layout.addLayout(info_layout)
        
        # 推荐理由
        self.content_layout.addWidget(QLabel("推荐理由:"))
        self.reason_text = QTextEdit()
        self.reason_text.setReadOnly(True)
        self.reason_text.setMaximumHeight(100)
        self.content_layout.addWidget(self.reason_text)
        
        # 照片
        # self.content_layout.addWidget(QLabel("美食照片:"))  # 删除这一行
        
        # 创建照片滚动区域
        self.photo_scroll = QScrollArea()
        self.photo_scroll.setWidgetResizable(True)
        self.photo_scroll.setMinimumHeight(150)
        
        # 照片容器
        self.photo_container = QWidget()
        self.photo_layout = QHBoxLayout(self.photo_container)
        self.photo_layout.setAlignment(Qt.AlignLeft)
        
        self.photo_scroll.setWidget(self.photo_container)
        self.content_layout.addWidget(self.photo_scroll)
        
        # 将内容布局添加到主布局
        self.main_layout.addLayout(self.content_layout)
    
    def display_food_details(self, food_item):
        """显示美食详情"""
        self.current_food_id = food_item["id"]
        
        # 清除现有内容
        self.clear_layout(self.photo_layout)
        
        # 设置标题
        self.name_label.setText(food_item["name"])
        
        # 设置基本信息
        info_items = [
            ("城市:", food_item["city"]),
            ("评分:", f"{food_item['rating']} / 10"),
            ("地址:", food_item["address"]),
            ("坐标:", f"({food_item['latitude']:.6f}, {food_item['longitude']:.6f})"),
            ("添加时间:", food_item["created_at"].split("T")[0])
        ]
        
        for row, (label, value) in enumerate(info_items):
            self.city_label.setText(f"{label} {value}")
        
        # 设置推荐理由
        reason_text = food_item.get("reason", "")
        if reason_text:
            self.reason_text.setPlainText(reason_text)
            self.reason_text.show()
        else:
            self.reason_text.hide()
        
        # 加载照片
        self.load_photos(food_item["id"])
    
    def load_photos(self, food_id):
        """加载美食照片"""
        # 清除现有照片
        while self.photo_layout.count():
            item = self.photo_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not food_id:
            return
        
        # 获取照片数据
        conn = None
        try:
            conn = self.food_manager.get_connection()
            cursor = conn.cursor()
            
            # 查询所有相关照片 - 确保使用正确的表名
            cursor.execute("SELECT id, photo_data FROM photos WHERE food_item_id = ?", (food_id,))
            photos = cursor.fetchall()
            
            if not photos:
                # 没有照片时不显示任何内容
                # 不显示"暂无照片"文本，让界面更加简洁
                return
            
            # 显示每张照片
            for photo_id, photo_data in photos:
                pixmap = QPixmap()
                if pixmap.loadFromData(photo_data):
                    # 等比例缩放到合适大小
                    pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    photo_label = QLabel()
                    photo_label.setPixmap(pixmap)
                    photo_label.setFixedSize(200, 150)
                    photo_label.setScaledContents(False)
                    photo_label.setAlignment(Qt.AlignCenter)
                    photo_label.setStyleSheet("border: 1px solid #ccc; margin: 5px;")
                    
                    self.photo_layout.addWidget(photo_label)
                else:
                    print(f"无法加载照片ID: {photo_id}")
            
            # 添加弹性空间
            self.photo_layout.addStretch()
        
        except Exception as e:
            print(f"加载照片错误: {e}")
        
        finally:
            if conn:
                conn.close()
    
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
        self.name_label.setText("请选择美食项")
        self.clear_layout(self.photo_layout)
        self.reason_text.hide()
    
    def set_food_data(self, food_data):
        """设置美食数据并更新显示"""
        self.food_data = food_data
        
        # 更新标题和基本信息
        self.name_label.setText(food_data.get("name", "未知"))
        self.rating_label.setText(f"评分: {food_data.get('rating', 0)}")
        self.city_label.setText(f"城市: {food_data.get('city', '未知')}")
        self.address_label.setText(f"地址: {food_data.get('address', '未知')}")
        
        # 更新类型信息
        food_type = food_data.get("food_type", "")
        if food_type:
            self.type_label.setText(f"类型: {food_type}")
            self.type_label.setVisible(True)
        else:
            self.type_label.setVisible(False)
        
        # 更新推荐理由
        reason = food_data.get("reason", "")
        if reason:
            self.reason_text.setPlainText(reason)
        else:
            self.reason_text.setPlainText("暂无推荐理由")
        
        # 加载照片
        self.load_photos(food_data.get("id")) 