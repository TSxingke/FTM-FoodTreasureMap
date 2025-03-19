import sqlite3
import os

def initialize_database():
    """初始化数据库，创建必要的表"""
    db_path = "data/food_map.db"
    
    # 检查数据库文件是否存在
    db_exists = os.path.exists(db_path)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 如果数据库不存在，创建表
    if not db_exists:
        # 创建美食店铺表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            rating INTEGER NOT NULL,
            reason TEXT,
            address TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')
        
        # 创建照片表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_id INTEGER NOT NULL,
            photo_data BLOB NOT NULL,
            FOREIGN KEY (food_id) REFERENCES food_items (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建标签表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        ''')
        
        # 创建美食-标签关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_tags (
            food_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (food_id, tag_id),
            FOREIGN KEY (food_id) REFERENCES food_items (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
        ''')
        
        # 提交更改
        conn.commit()
    
    # 关闭连接
    conn.close()
    
    return db_path 