from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
import json
import requests
import os

class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.api_key = "IwROZMfGJmOcfruwdxtDtEAPFtyQPJp3"
        self.api_key_gl = "OBUkmzeyCj9vCfell3YPGqKGN47Sj9LJ"
        self.view_mode = "country"  # 默认全国视图
        self.current_city = "北京"   # 默认城市
        
        self.setup_ui()
        self.initialize_map()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 顶部控制栏
        control_layout = QHBoxLayout()
        
        # 城市选择
        control_layout.addWidget(QLabel("当前城市:"))
        self.city_combo = QComboBox()
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州"])
        self.city_combo.currentTextChanged.connect(self.on_city_changed)
        control_layout.addWidget(self.city_combo)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 地图视图
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
    
    def initialize_map(self):
        # 创建本地HTML文件
        html_file_path = os.path.join(os.path.dirname(__file__), "map.html")
        
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
            <script type="text/javascript" src="https://api.map.baidu.com/api?type=webgl&v=1.0&ak={self.api_key_gl}"></script>
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
                    map = new BMapGL.Map("map-container");
                    var point = new BMapGL.Point(116.404, 39.915); // 默认北京
                    map.centerAndZoom(point, 5);  // 全国视图
                    
                    // 启用滚轮缩放和平移
                    map.enableScrollWheelZoom();
                    map.enableDragging();
                    
                    // 添加控件
                    map.addControl(new BMapGL.NavigationControl());
                    map.addControl(new BMapGL.ScaleControl());
                    
                    // 添加测试标记
                    setTimeout(function() {{
                        addFoodMarker(116.404, 39.915, "测试点", 8, 0);
                    }}, 1000);
                }}
                
                // 添加食物标记
                function addFoodMarker(lng, lat, name, rating, id) {{
                    var point = new BMapGL.Point(lng, lat);
                    
                    // 根据评分设置颜色
                    var color = getColorByRating(rating);
                    
                    // 创建标记
                    var marker = new BMapGL.Marker(point);
                    marker.setTitle(name);
                    
                    // 添加点击事件
                    marker.addEventListener("click", function() {{
                        alert("点击了: " + name + " (评分: " + rating + ")");
                    }});
                    
                    // 添加到地图
                    map.addOverlay(marker);
                    markers.push(marker);
                    
                    // 添加探索范围圆
                    var radius = (viewMode === "city") ? 1000 : 10000;
                    var circle = new BMapGL.Circle(point, radius, {{
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
                    var myGeo = new BMapGL.Geocoder();
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
                    // 实现高亮逻辑
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
        self.view_mode = mode
        # 调用JavaScript函数更新视图模式
        self.web_view.page().runJavaScript(f"setViewMode('{mode}');")
        
        # 更新地图上的标记
        self.refresh_map()
    
    def on_city_changed(self, city_name):
        self.current_city = city_name
        # 调用JavaScript函数更新城市
        self.web_view.page().runJavaScript(f"setCity('{city_name}');")
        
        # 如果是城市视图，则只显示当前城市的美食点
        if self.view_mode == "city":
            self.refresh_map()
    
    def plot_food_locations(self, food_items):
        # 清除现有标记
        self.web_view.page().runJavaScript("clearMarkers();")
        
        # 添加新标记
        for item in food_items:
            # 如果是城市视图且不是当前城市，则跳过
            if self.view_mode == "city" and item['city'] != self.current_city:
                continue
                
            # 添加标记
            js_code = f"addFoodMarker({item['longitude']}, {item['latitude']}, '{item['name']}', {item['rating']}, {item['id']});"
            self.web_view.page().runJavaScript(js_code)
    
    def highlight_food_location(self, food_item):
        # 高亮显示选中的美食点
        self.web_view.page().runJavaScript(f"highlightMarker({food_item['id']});")
    
    def refresh_map(self):
        # 重新加载所有美食点
        from data.food_manager import FoodManager
        food_manager = FoodManager()
        food_items = food_manager.get_all_food_items()
        self.plot_food_locations(food_items) 