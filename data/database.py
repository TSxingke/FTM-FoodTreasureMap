import sqlite3
import os
import datetime

def get_connection():
    """获取数据库连接"""
    # 确保数据目录存在
    data_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(data_dir, exist_ok=True)
    
    # 数据库文件路径
    db_path = os.path.join(data_dir, "food_map.db")
    
    # 创建连接
    conn = sqlite3.connect(db_path)
    
    return conn

def initialize_database():
    """初始化数据库"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='food_items'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # 检查表结构，是否需要升级
            cursor.execute("PRAGMA table_info(food_items)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            # 如果需要添加新列或修改表结构
            need_migration = False
            
            # 检查是否需要添加 is_imported 列
            if "is_imported" not in column_names:
                need_migration = True
            
            # 检查是否需要迁移
            if need_migration:
                # 创建临时表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS food_items_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    address TEXT,
                    latitude REAL,
                    longitude REAL,
                    rating REAL,
                    reason TEXT,
                    collection_id INTEGER,
                    food_type TEXT,
                    is_imported INTEGER DEFAULT 0,
                    FOREIGN KEY (collection_id) REFERENCES map_collections(id)
                )
                """)
                
                # 列出现有的表列名
                existing_cols = ", ".join(column_names)
                
                # 在老数据中，添加默认的 is_imported 值
                if "is_imported" not in column_names:
                    # 使用指定的列名直接插入数据
                    cursor.execute(f"""
                    INSERT INTO food_items_temp 
                    (id, name, city, address, latitude, longitude, rating, reason, collection_id, food_type, is_imported)
                    SELECT id, name, city, address, latitude, longitude, rating, reason, collection_id, food_type, 0
                    FROM food_items
                    """)
                
                # 删除旧表并重命名新表
                cursor.execute("DROP TABLE food_items")
                cursor.execute("ALTER TABLE food_items_temp RENAME TO food_items")
                
                print("食品数据表已成功升级")
            
        else:
            # 创建食品集合表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS map_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_personal INTEGER DEFAULT 0
            )
            """)
            
            # 创建默认的个人集合
            cursor.execute("""
            INSERT INTO map_collections (name, description, is_personal)
            VALUES ('我的美食地图', '个人美食收藏', 1)
            """)
            
            # 创建食品记录表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                address TEXT,
                latitude REAL,
                longitude REAL,
                rating REAL,
                reason TEXT,
                collection_id INTEGER,
                food_type TEXT,
                is_imported INTEGER DEFAULT 0,
                FOREIGN KEY (collection_id) REFERENCES map_collections(id)
            )
            """)
            
            print("食品数据表已成功创建")
        
        # 创建照片表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_item_id INTEGER,
            photo_data BLOB,
            FOREIGN KEY (food_item_id) REFERENCES food_items(id)
        )
        """)
        
        # 创建城市表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)
        
        # 初始添加一些常用城市
        cities = ["北京", "上海", "广州", "深圳", "成都", "杭州"]
        for city in cities:
            try:
                cursor.execute("INSERT INTO cities (name) VALUES (?)", (city,))
            except:
                pass  # 忽略已存在的城市
        
        conn.commit()
        
    except Exception as e:
        print(f"初始化数据库错误: {e}")
        if conn:
            conn.rollback()
        raise
    
    finally:
        if conn:
            conn.close()
    
    return "data/food_map.db" 