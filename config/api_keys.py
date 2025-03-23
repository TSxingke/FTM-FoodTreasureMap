# 百度地图API密钥配置

import os
import json

# 用于地点检索的API密钥
PLACE_SEARCH_AK = ""

# 用于地图显示的API密钥
MAP_DISPLAY_AK = ""

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")

def load_config():
    """加载配置文件"""
    global PLACE_SEARCH_AK, MAP_DISPLAY_AK
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            PLACE_SEARCH_AK = config.get("PLACE_SEARCH_AK", "")
            MAP_DISPLAY_AK = config.get("MAP_DISPLAY_AK", "")
        except Exception as e:
            print(f"加载配置文件失败: {e}")

def save_config(place_search_ak, map_display_ak):
    """保存配置文件"""
    global PLACE_SEARCH_AK, MAP_DISPLAY_AK
    
    # 更新全局变量
    PLACE_SEARCH_AK = place_search_ak
    MAP_DISPLAY_AK = map_display_ak
    
    # 确保目录存在
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    
    try:
        config = {
            "PLACE_SEARCH_AK": place_search_ak,
            "MAP_DISPLAY_AK": map_display_ak
        }
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

# 初始化时加载配置
load_config()