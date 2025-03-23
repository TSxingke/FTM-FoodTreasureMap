from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
import json
import requests
import os

from config.api_keys import PLACE_SEARCH_AK
from config.api_keys import MAP_DISPLAY_AK

class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        
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
        
        # 顶部控制栏
        control_layout = QHBoxLayout()
        
        # 城市选择
        control_layout.addWidget(QLabel("当前城市:"))
        self.city_combo = QComboBox()
        # 改为只读模式
        self.city_combo.setEditable(False)
        self.city_combo.addItems(["北京", "上海", "广州", "深圳", "成都", "杭州"])
        self.city_combo.currentTextChanged.connect(self.on_city_changed)
        control_layout.addWidget(self.city_combo)
        
        # 添加城市管理按钮
        manage_cities_btn = QPushButton("城市管理")
        manage_cities_btn.clicked.connect(self.show_city_manager)
        control_layout.addWidget(manage_cities_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 地图视图
        self.web_view = QWebEngineView()
        
        # 添加以下代码，启用跨域访问
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
    
    def initialize_map(self):
        # 创建本地HTML文件
        html_file_path = os.path.join(os.path.dirname(__file__), "map.html")
        
        # 创建HTML内容 - 注意这里使用 {{ 和 }} 来转义 JavaScript 中的 ${ 和 }
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
            <script>
                window.HOST_TYPE = '2';
                window.BMapGL_loadScriptTime = (new Date).getTime();
            </script>
            <script type="text/javascript" src="https://api.map.baidu.com/getscript?type=webgl&v=1.0&ak={self.api_key_gl}&services=&t=20250313124310"></script>
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
                }}
                
                // 添加食物标记
                function addFoodMarker(lng, lat, name, rating, id, address, reason, city, food_type) {{
                    var point = new BMapGL.Point(lng, lat);
                    
                    // 根据评分设置颜色
                    var color = getColorByRating(rating);
                    
                    // 创建标记
                    var marker = new BMapGL.Marker(point);
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
                        // 关闭之前的信息窗口
                        if (map.infoWindow) {{
                            map.closeInfoWindow();
                        }}
                        
                        // 创建信息卡片内容
                        var content = `
                            <div style="background-color: rgba(255, 255, 255, 0.8); 
                                        padding: 15px; 
                                        border-radius: 8px; 
                                        max-width: 300px;
                                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);">
                                <h3 style="margin-top: 0; color: ${{color}};">${{name}}</h3>
                                <div style="margin-bottom: 8px;">
                                    <span style="font-weight: bold;">评分: </span>
                                    <span>${{rating}} / 10</span>
                                </div>
                                <div style="margin-bottom: 8px;">
                                    <span style="font-weight: bold;">类型: </span>
                                    <span>${{food_type}}</span>
                                </div>
                                <div style="margin-bottom: 8px;">
                                    <span style="font-weight: bold;">地址: </span>
                                    <span>${{address}}</span>
                                </div>
                                <div style="margin-bottom: 8px;">
                                    <span style="font-weight: bold;">城市: </span>
                                    <span>${{city}}</span>
                                </div>
                                <div>
                                    <span style="font-weight: bold;">推荐理由: </span>
                                    <div style="margin-top: 5px;">${{reason}}</div>
                                </div>
                            </div>
                        `;
                        
                        // 创建并打开信息窗口
                        var infoWindow = new BMapGL.InfoWindow(content, {{
                            width: 320,
                            height: 200,
                            title: "",
                            enableMessage: false,
                            enableCloseOnClick: true
                        }});
                        
                        map.infoWindow = infoWindow;
                        marker.openInfoWindow(infoWindow, point);
                        
                        // 通知Python应用高亮显示此美食点
                        window.pywebview.api.highlightFoodItem(id);
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
        # 检查地图是否已经加载
        check_js = """
        if (typeof map !== 'undefined' && typeof addFoodMarker === 'function' && typeof clearMarkers === 'function') {
            clearMarkers();
            true;
        } else {
            false;
        }
        """
        
        def on_check_result(result):
            if result:
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
                        "{item['food_type']}"
                    );"""
                    self.web_view.page().runJavaScript(js_code)
            else:
                # 如果地图还没准备好，延迟200ms再试
                QTimer.singleShot(200, lambda: self.plot_food_locations(food_items))
        
        self.web_view.page().runJavaScript(check_js, on_check_result)
    
    def highlight_food_location(self, food_item):
        # 高亮显示选中的美食点
        self.web_view.page().runJavaScript(f"highlightMarker({food_item['id']});")
    
    def refresh_map(self):
        # 重新加载所有美食点
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