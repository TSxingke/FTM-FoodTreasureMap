from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QPushButton, QProgressBar
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtGui import QIcon
import json
import requests
import os

from config.api_keys import PLACE_SEARCH_AK
from config.api_keys import MAP_DISPLAY_AK

class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 设置基本样式
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                min-width: 150px;
            }
            QPushButton {
                background-color: #ff7043;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5722;
            }
        """)
        
        self.api_key = "IwROZMfGJmOcfruwdxtDtEAPFtyQPJp3"
        self.api_key_gl = MAP_DISPLAY_AK
        self.view_mode = "country"  # 默认全国视图
        self.current_city = "北京"   # 默认城市
        
        self.setup_ui()
        self.initialize_map()
        
        # 加载保存的城市列表
        self.load_cities()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # 减少间距以最大化地图区域
        
        # 添加控制面板
        control_panel = QWidget()
        control_panel.setMaximumHeight(40)  # 减小控制面板高度
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # 城市选择控件
        city_label = QLabel("当前城市:")
        city_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(city_label)
        
        self.city_combo = QComboBox()
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州", "武汉", "西安", "南京", "重庆"])
        self.city_combo.currentTextChanged.connect(self.on_city_changed)
        control_layout.addWidget(self.city_combo)
        
        # 添加刷新按钮
        refresh_btn = QPushButton("刷新地图")
        refresh_btn.setIcon(QIcon("icons/refresh.png"))
        refresh_btn.clicked.connect(self.refresh_map)
        control_layout.addWidget(refresh_btn)
        
        # 添加弹性空间
        control_layout.addStretch(1)
        
        # 添加视图切换标签
        view_label = QLabel("视图模式:")
        view_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(view_label)
        
        # 添加视图切换按钮
        country_btn = QPushButton("全国视图")
        country_btn.clicked.connect(lambda: self.set_view_mode("country"))
        control_layout.addWidget(country_btn)
        
        city_btn = QPushButton("城市视图")
        city_btn.clicked.connect(lambda: self.set_view_mode("city"))
        control_layout.addWidget(city_btn)
        
        layout.addWidget(control_panel)
        
        # 地图视图
        self.web_view = QWebEngineView()
        self.web_view.page().profile().clearHttpCache()
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f5f5f5;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #ff7043;
                border-radius: 2px;
            }
        """)
        
        self.web_view.loadProgress.connect(self.progress_bar.setValue)
        self.web_view.loadFinished.connect(lambda: self.progress_bar.setVisible(False))
        self.web_view.loadStarted.connect(lambda: self.progress_bar.setVisible(True))
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
        
        # 初始化地图
        self.food_markers = []
    
    def initialize_map(self):
        """初始化地图"""
        # 确定HTML文件路径
        html_dir = os.path.dirname(os.path.abspath(__file__))
        html_file_path = os.path.join(html_dir, "map.html")
        
        # 创建HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>美食地图</title>
            <style>
                html, body, #map-container {{
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }}
            </style>
            <script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak={self.api_key_gl}"></script>
        </head>
        <body>
            <div id="map-container"></div>
            <script>
                // 全局变量
                var map;
                var viewMode = "country";
                var markers = [];
                
                // 初始化地图
                function initMap() {{
                    map = new BMap.Map("map-container");
                    var point = new BMap.Point(116.404, 39.915); // 默认北京
                    map.centerAndZoom(point, 5);  // 全国视图
                    
                    // 启用滚轮缩放和平移
                    map.enableScrollWheelZoom();
                    map.enableDragging();
                    
                    // 添加控件
                    map.addControl(new BMap.NavigationControl());
                    map.addControl(new BMap.ScaleControl());
                }}
                
                // 添加食物标记
                function addFoodMarker(lng, lat, name, rating, id, address, reason, city, food_type) {{
                    var point = new BMap.Point(lng, lat);
                    
                    // 根据评分设置颜色
                    var color = getColorByRating(rating);
                    
                    // 创建标记
                    var marker = new BMap.Marker(point);
                    marker.setTitle(name);
                    
                    // 存储美食点数据
                    marker.foodData = {{
                        id: id,
                        name: name,
                        rating: rating,
                        address: address,
                        reason: reason || "暂无推荐理由",
                        city: city,
                        food_type: food_type
                    }};
                    
                    // 添加点击事件
                    marker.addEventListener("click", function() {{
                        // 创建信息卡片内容
                        var content = `
                            <div style="width: 280px; overflow: hidden;">
                                <h3 style="margin-top: 0; margin-bottom: 8px;">${{name}}</h3>
                                <div>
                                    <span style="font-weight: bold;">评分: </span>
                                    <span>${{rating}} / 10</span>
                                </div>
                                <div>
                                    <span style="font-weight: bold;">类型: </span>
                                    <span>${{food_type}}</span>
                                </div>
                                <div>
                                    <span style="font-weight: bold;">地址: </span>
                                    <span>${{address}}</span>
                                </div>
                                <div>
                                    <span style="font-weight: bold;">城市: </span>
                                    <span>${{city}}</span>
                                </div>
                                <div>
                                    <span style="font-weight: bold;">推荐理由: </span>
                                    <div style="margin-top: 5px;">${{reason}}</div>
                                </div>
                            </div>
                        `;
                        
                        // 创建信息窗口
                        var infoWindow = new BMap.InfoWindow(content);
                        marker.openInfoWindow(infoWindow);
                    }});
                    
                    // 添加到地图
                    map.addOverlay(marker);
                    markers.push(marker);
                    
                    // 添加探索范围圆
                    var radius = (viewMode === "city") ? 1000 : 10000;
                    var circle = new BMap.Circle(point, radius, {{
                        strokeColor: color,
                        strokeWeight: 1,
                        strokeOpacity: 0.5,
                        fillColor: color,
                        fillOpacity: 0.2
                    }});
                    
                    map.addOverlay(circle);
                    
                    return marker;
                }}
                
                // 根据评分获取颜色
                function getColorByRating(rating) {{
                    if (rating >= 9) return "#FF4500";  // 橙红色
                    if (rating >= 8) return "#FF8C00";  // 深橙色
                    if (rating >= 7) return "#FFD700";  // 金色
                    if (rating >= 6) return "#9ACD32";  // 黄绿色
                    if (rating >= 5) return "#32CD32";  // 酸橙绿
                    return "#1E90FF";                   // 道奇蓝
                }}
                
                // 设置视图模式
                function setViewMode(mode) {{
                    viewMode = mode;
                    if (mode === "country") {{
                        map.setZoom(5);
                    }} else {{
                        map.setZoom(12);
                    }}
                }}
                
                // 设置城市
                function setCity(cityName) {{
                    var myGeo = new BMap.Geocoder();
                    myGeo.getPoint(cityName, function(point) {{
                        if (point) {{
                            map.centerAndZoom(point, viewMode === "country" ? 5 : 12);
                        }}
                    }}, cityName);
                }}
                
                // 清除所有标记
                function clearMarkers() {{
                    for (var i = 0; i < markers.length; i++) {{
                        map.removeOverlay(markers[i]);
                    }}
                    markers = [];
                    map.clearOverlays();
                }}
                
                // 高亮显示标记
                function highlightMarker(id) {{
                    // 查找对应的标记
                    for (var i = 0; i < markers.length; i++) {{
                        if (markers[i].foodData && markers[i].foodData.id == id) {{
                            // 简单地将地图中心移动到标记位置
                            var point = markers[i].getPosition();
                            map.panTo(point);
                            break;
                        }}
                    }}
                }}
                
                // 通过ID显示信息窗口
                function showInfoWindowById(id) {{
                    for (var i = 0; i < markers.length; i++) {{
                        if (markers[i].foodData && markers[i].foodData.id == id) {{
                            // 模拟点击事件
                            var e = document.createEvent('MouseEvents');
                            e.initEvent('click', true, true);
                            markers[i].dispatchEvent(e);
                            break;
                        }}
                    }}
                }}
                
                // 页面加载完成后初始化地图
                window.onload = initMap;
            </script>
        </body>
        </html>
        """
        
        # 写入HTML文件
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # 加载本地HTML文件
        self.web_view.load(QUrl.fromLocalFile(html_file_path))
    
    def set_view_mode(self, mode):
        """设置视图模式"""
        self.view_mode = mode
        # 调用JavaScript函数更新视图模式
        self.web_view.page().runJavaScript(f"setViewMode('{mode}');")
        
        # 更新地图上的标记
        self.refresh_map()
    
    def on_city_changed(self, city_name):
        """城市改变时调用"""
        self.current_city = city_name
        # 调用JavaScript函数更新城市
        self.web_view.page().runJavaScript(f"setCity('{city_name}');")
        
        # 如果是城市视图，则只显示当前城市的美食点
        if self.view_mode == "city":
            self.refresh_map()
    
    def plot_food_locations(self, food_items):
        """在地图上绘制美食位置"""
        # 清除现有标记
        self.web_view.page().runJavaScript("clearMarkers();")
        
        # 添加新标记
        for item in food_items:
            # 如果是城市视图且不是当前城市，则跳过
            if self.view_mode == "city" and item['city'] != self.current_city:
                continue
                
            # 添加标记，传递更多信息以便显示在悬浮卡片上
            reason = item.get('reason', '')
            # 处理字符串中的引号，避免JavaScript错误
            reason = reason.replace('"', '\\"').replace("'", "\\'")
            name = item['name'].replace('"', '\\"').replace("'", "\\'")
            address = item.get('address', '未知').replace('"', '\\"').replace("'", "\\'")
            city = item.get('city', '未知').replace('"', '\\"').replace("'", "\\'")
            
            js_code = f"""addFoodMarker(
                {item['longitude']}, 
                {item['latitude']}, 
                "{name}", 
                {item['rating']}, 
                {item['id']},
                "{address}",
                "{reason}",
                "{city}",
                "{item.get('food_type', '其他')}"
            );"""
            self.web_view.page().runJavaScript(js_code)
    
    def highlight_food_location(self, food_item):
        """高亮显示选中的美食点"""
        self.web_view.page().runJavaScript(f"highlightMarker({food_item['id']});")
    
    def refresh_map(self):
        """刷新地图标记"""
        from data.food_manager import FoodManager
        food_manager = FoodManager()
        food_items = food_manager.get_all_food_items()
        self.plot_food_locations(food_items)
    
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
            
            # 清除现有项
            self.city_combo.clear()
                
            # 添加城市
            for city in cities:
                if city:
                    self.city_combo.addItem(city)
                    
            # 如果没有城市，添加默认城市
            if self.city_combo.count() == 0:
                self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州"])
        
        except Exception as e:
            print(f"加载城市列表失败: {e}")
        
        finally:
            if conn:
                conn.close()

    def show_city_manager(self):
        """显示城市管理对话框"""
        from ui.city_dialog import CityDialog
        
        # 获取现有城市列表
        cities = []
        for i in range(self.city_combo.count()):
            cities.append(self.city_combo.itemText(i))
        
        dialog = CityDialog(self, existing_cities=cities)
        if dialog.exec_():
            # 获取更新后的城市列表
            updated_cities = dialog.get_cities()
            
            # 更新城市下拉框
            current_city = self.city_combo.currentText()
            self.city_combo.clear()
            self.city_combo.addItems(updated_cities)
            
            # 尝试恢复选中的城市
            index = self.city_combo.findText(current_city)
            if index >= 0:
                self.city_combo.setCurrentIndex(index)
            
            # 保存城市列表到配置文件
            self.save_cities(updated_cities)

    def save_cities(self, cities):
        """保存城市列表到配置文件"""
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
            os.makedirs(config_dir, exist_ok=True)
            
            config_path = os.path.join(config_dir, "cities.json")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(cities, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"Error saving cities: {e}")

    def load_cities(self):
        """从配置文件加载城市列表"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "cities.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    cities = json.load(f)
                
                # 更新城市下拉框
                self.city_combo.clear()
                self.city_combo.addItems(cities)
        
        except Exception as e:
            print(f"Error loading cities: {e}")

    def show_food_info_window(self, food_id):
        """在地图上显示指定食物的信息窗口"""
        js_code = f"showInfoWindowById({food_id});"
        self.web_view.page().runJavaScript(js_code) 