import sqlite3
import json
import os
import datetime
import csv
import base64

class FoodManager:
    def __init__(self, db_path="data/food_map.db"):
        self.db_path = db_path
        
        # 获取或创建默认的个人集合ID
        self.personal_collection_id = self.get_personal_collection_id()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def get_personal_collection_id(self):
        """获取个人集合ID，如果不存在则创建"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 查询个人集合
            cursor.execute("SELECT id FROM map_collections WHERE is_personal = 1 LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # 创建个人集合
                cursor.execute('''
                INSERT INTO map_collections (name, description, is_personal, created_at)
                VALUES (?, ?, ?, ?)
                ''', ("我的美食地图", "个人美食收藏", 1, datetime.datetime.now().isoformat()))
                
                conn.commit()
                return cursor.lastrowid
        
        except Exception as e:
            print(f"Error getting personal collection: {e}")
            return 1  # 默认ID
        
        finally:
            if conn:
                conn.close()
    
    def add_food_item(self, food_data, collection_id=None):
        """添加新的美食记录到指定集合"""
        if collection_id is None:
            collection_id = self.personal_collection_id
            
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 插入美食记录
            cursor.execute("""
                INSERT INTO food_items 
                (collection_id, name, city, rating, reason, address, latitude, longitude, food_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_id,
                food_data["name"],
                food_data["city"],
                food_data["rating"],
                food_data["reason"],
                food_data["address"],
                food_data["latitude"],
                food_data["longitude"],
                food_data["food_type"],
                datetime.datetime.now().isoformat()
            ))
            
            food_id = cursor.lastrowid
            
            # 插入照片
            for photo_data in food_data["photos"]:
                cursor.execute("""
                    INSERT INTO food_photos (food_id, photo_data)
                    VALUES (?, ?)
                """, (food_id, photo_data))
            
            conn.commit()
            return food_id
        
        except Exception as e:
            print(f"Error adding food item: {e}")
            if conn:
                conn.rollback()
            return None
        
        finally:
            if conn:
                conn.close()
    
    def get_all_food_items(self):
        """获取所有美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, city, rating, reason, address, 
                       latitude, longitude, food_type, created_at
                FROM food_items
                ORDER BY created_at DESC
            """)
            
            food_items = []
            for row in cursor.fetchall():
                item = dict(row)
                
                # 获取照片ID列表
                cursor.execute("""
                    SELECT id FROM food_photos
                    WHERE food_id = ?
                """, (item["id"],))
                
                photo_ids = [photo_id[0] for photo_id in cursor.fetchall()]
                item["photo_ids"] = photo_ids
                
                food_items.append(item)
            
            return food_items
        
        except Exception as e:
            print(f"Error getting food items: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def get_food_item(self, food_id):
        """根据ID获取单个美食项"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
            cursor = conn.cursor()
            
            # 查询美食记录
            cursor.execute("SELECT * FROM food_items WHERE id = ?", (food_id,))
            row = cursor.fetchone()
            
            if row:
                food_item = dict(row)
                
                # 查询照片
                cursor.execute("SELECT id FROM food_photos WHERE food_id = ?", (food_id,))
                photo_ids = [row[0] for row in cursor.fetchall()]
                food_item["photo_ids"] = photo_ids
                
                return food_item
            
            return None
        
        except Exception as e:
            print(f"Error getting food item: {e}")
            return None
        
        finally:
            if conn:
                conn.close()
    
    def get_photo(self, photo_id):
        """获取指定ID的照片数据"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT photo_data FROM food_photos
                WHERE id = ?
            """, (photo_id,))
            
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        
        except Exception as e:
            print(f"Error getting photo {photo_id}: {e}")
            return None
        
        finally:
            if conn:
                conn.close()
    
    def delete_food_item(self, food_id):
        """删除美食记录及其相关照片"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 先删除与该美食点关联的所有照片
            cursor.execute("DELETE FROM photos WHERE food_item_id = ?", (food_id,))
            
            # 然后删除美食点记录
            cursor.execute("DELETE FROM food_items WHERE id = ?", (food_id,))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"Error deleting food item: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if conn:
                conn.close()
    
    def update_food_item(self, food_id, food_data):
        """更新美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 更新美食记录 - 确保包含所有需要更新的字段
            cursor.execute("""
                UPDATE food_items 
                SET name = ?, city = ?, rating = ?, reason = ?, 
                    address = ?, latitude = ?, longitude = ?, 
                    food_type = ?, collection_id = ?
                WHERE id = ?
            """, (
                food_data["name"],
                food_data["city"],
                food_data["rating"],
                food_data["reason"],
                food_data["address"],
                food_data["latitude"],
                food_data["longitude"],
                food_data["food_type"],
                food_data.get("collection_id", self.personal_collection_id),
                food_id
            ))
            
            conn.commit()
            return True
        
        except Exception as e:
            print(f"Error updating food item: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if conn:
                conn.close()
    
    def get_food_by_city(self, city):
        """获取指定城市的所有美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, city, rating, reason, address, 
                       latitude, longitude, created_at
                FROM food_items
                WHERE city = ?
                ORDER BY rating DESC
            """, (city,))
            
            food_items = []
            for row in cursor.fetchall():
                food_items.append(dict(row))
            
            return food_items
        
        except Exception as e:
            print(f"Error getting food items for city {city}: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def get_food_by_rating(self, min_rating):
        """获取评分不低于指定值的所有美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, city, rating, reason, address, 
                       latitude, longitude, created_at
                FROM food_items
                WHERE rating >= ?
                ORDER BY rating DESC
            """, (min_rating,))
            
            food_items = []
            for row in cursor.fetchall():
                food_items.append(dict(row))
            
            return food_items
        
        except Exception as e:
            print(f"Error getting food items with rating >= {min_rating}: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def export_data(self, file_path):
        """导出美食数据到文件"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取所有美食记录
            cursor.execute("""
                SELECT id, name, city, rating, reason, address, 
                       latitude, longitude, food_type, created_at
                FROM food_items
                ORDER BY created_at DESC
            """)
            
            food_items = []
            for row in cursor.fetchall():
                food_item = dict(row)
                
                # 获取照片数据
                cursor.execute("""
                    SELECT id, photo_data FROM food_photos
                    WHERE food_id = ?
                """, (food_item["id"],))
                
                photos = []
                for photo_row in cursor.fetchall():
                    # 将二进制照片数据转换为base64编码
                    photo_data = photo_row[1]
                    photo_base64 = base64.b64encode(photo_data).decode('utf-8')
                    photos.append({
                        "id": photo_row[0],
                        "data": photo_base64
                    })
                
                food_item["photos"] = photos
                food_items.append(food_item)
            
            # 根据文件扩展名选择导出格式
            if file_path.endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(food_items, f, ensure_ascii=False, indent=2)
            
            elif file_path.endswith(".csv"):
                # CSV格式不适合导出照片数据，只导出基本信息
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    if food_items:
                        # 获取字段名（排除照片字段）
                        fieldnames = [key for key in food_items[0].keys() if key != 'photos']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for item in food_items:
                            row_data = {key: item[key] for key in fieldnames}
                            writer.writerow(row_data)
            
            else:
                # 默认使用JSON格式
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(food_items, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
    
    def get_personal_food_items(self):
        """获取用户自己的美食数据（非导入的）"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, city, rating, reason, address, 
                       latitude, longitude, food_type, created_at
                FROM food_items
                WHERE is_imported = 0
                ORDER BY created_at DESC
            """)
            
            food_items = []
            for row in cursor.fetchall():
                item = dict(row)
                
                # 获取照片ID列表
                cursor.execute("""
                    SELECT id FROM food_photos
                    WHERE food_id = ?
                """, (item["id"],))
                
                photo_ids = [photo_id[0] for photo_id in cursor.fetchall()]
                item["photo_ids"] = photo_ids
                
                food_items.append(item)
            
            return food_items
        
        except Exception as e:
            print(f"Error getting personal food items: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def get_imported_food_items(self):
        """获取导入的美食数据"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, city, rating, reason, address, 
                       latitude, longitude, food_type, created_at
                FROM food_items
                WHERE is_imported = 1
                ORDER BY created_at DESC
            """)
            
            food_items = []
            for row in cursor.fetchall():
                item = dict(row)
                
                # 获取照片ID列表
                cursor.execute("""
                    SELECT id FROM food_photos
                    WHERE food_id = ?
                """, (item["id"],))
                
                photo_ids = [photo_id[0] for photo_id in cursor.fetchall()]
                item["photo_ids"] = photo_ids
                
                food_items.append(item)
            
            return food_items
        
        except Exception as e:
            print(f"Error getting imported food items: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def import_data(self, file_path):
        """从文件导入美食数据"""
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        try:
            # 读取导入文件
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    try:
                        food_data = json.load(f)
                        
                        # 检查是否是我们的格式
                        if isinstance(food_data, dict) and 'food_items' in food_data:
                            # 新格式，包含元数据
                            food_items = food_data['food_items']
                        else:
                            # 老格式或直接的数组
                            food_items = food_data if isinstance(food_data, list) else [food_data]
                    except json.JSONDecodeError:
                        return False, "JSON 格式错误，无法解析文件"
                else:
                    return False, "不支持的文件格式，请使用.json文件"
            
            # 连接数据库
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            
            successful_imports = 0
            
            for item in food_items:
                try:
                    # 确保item是字典
                    if not isinstance(item, dict):
                        print(f"跳过非字典项: {item}")
                        continue
                    
                    # 检查是否已存在相同名称和地址的记录
                    cursor.execute("""
                        SELECT id FROM food_items 
                        WHERE name = ? AND address = ?
                    """, (item.get('name', ''), item.get('address', '')))
                    
                    existing_id = cursor.fetchone()
                    
                    if existing_id:
                        # 跳过已存在的记录
                        continue
                    
                    # 插入新记录，标记为导入的数据
                    cursor.execute("""
                        INSERT INTO food_items 
                        (name, city, rating, reason, address, latitude, longitude, food_type, is_imported, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """, (
                        item.get('name', '未知店铺'),
                        item.get('city', '未知城市'),
                        float(item.get('rating', 5)),
                        item.get('reason', ''),
                        item.get('address', '未知地址'),
                        float(item.get('latitude', 0)),
                        float(item.get('longitude', 0)),
                        item.get('food_type', '其他'),
                        item.get('created_at', datetime.datetime.now().isoformat())
                    ))
                    
                    # 获取新插入记录的ID
                    food_id = cursor.lastrowid
                    
                    # 处理照片
                    if 'photos' in item and item['photos']:
                        for photo in item['photos']:
                            try:
                                if isinstance(photo, dict) and 'data' in photo:
                                    # 将base64编码的照片数据转换回二进制
                                    photo_data = base64.b64decode(photo['data'])
                                    
                                    cursor.execute("""
                                        INSERT INTO food_photos (food_id, photo_data)
                                        VALUES (?, ?)
                                    """, (food_id, photo_data))
                            except Exception as photo_error:
                                print(f"处理照片时出错: {photo_error}")
                    
                    successful_imports += 1
                    
                except Exception as item_error:
                    print(f"导入食品项时出错: {item_error}")
            
            # 提交事务
            conn.commit()
            
            return True, f"成功导入 {successful_imports} 条美食记录"
        
        except Exception as e:
            if conn:
                conn.rollback()
            return False, f"导入数据时出错: {str(e)}"
        
        finally:
            if conn:
                conn.close()
    
    def get_map_collections(self):
        """获取所有地图集合"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, description, is_personal, created_at
                FROM map_collections
                ORDER BY is_personal DESC, created_at DESC
            """)
            
            collections = []
            for row in cursor.fetchall():
                collections.append(dict(row))
            
            return collections
        
        except Exception as e:
            print(f"Error getting map collections: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def get_food_items_by_collection(self, collection_id):
        """获取指定集合的所有美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, city, rating, reason, address, 
                       latitude, longitude, food_type, created_at
                FROM food_items
                WHERE collection_id = ?
                ORDER BY created_at DESC
            """, (collection_id,))
            
            food_items = []
            for row in cursor.fetchall():
                item = dict(row)
                
                # 获取照片ID列表
                cursor.execute("""
                    SELECT id FROM food_photos
                    WHERE food_id = ?
                """, (item["id"],))
                
                photo_ids = [photo_id[0] for photo_id in cursor.fetchall()]
                item["photo_ids"] = photo_ids
                
                food_items.append(item)
            
            return food_items
        
        except Exception as e:
            print(f"Error getting food items for collection {collection_id}: {e}")
            return []
        
        finally:
            if conn:
                conn.close()
    
    def export_collection(self, collection_id, file_path):
        """导出地图集合到文件"""
        conn = None
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取集合信息
            cursor.execute("""
                SELECT name, description, created_at
                FROM map_collections
                WHERE id = ?
            """, (collection_id,))
            
            collection = dict(cursor.fetchone())
            
            # 获取美食项
            food_items = self.get_food_items_by_collection(collection_id)
            
            # 为每个食品项处理照片
            for item in food_items:
                # 获取照片数据
                photo_ids = item.pop("photo_ids", [])
                photos = []
                
                for photo_id in photo_ids:
                    photo_data = self.get_photo(photo_id)
                    if photo_data:
                        # 将二进制照片数据转换为base64编码
                        photo_base64 = base64.b64encode(photo_data).decode('utf-8')
                        photos.append({
                            "id": photo_id,
                            "data": photo_base64
                        })
                
                item["photos"] = photos
            
            # 创建导出数据
            export_data = {
                "metadata": {
                    "name": collection["name"],
                    "description": collection["description"],
                    "created_at": collection["created_at"],
                    "export_time": datetime.datetime.now().isoformat(),
                    "version": "2.0"
                },
                "food_items": food_items
            }
            
            # 导出为JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error exporting collection: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
    
    def import_collection(self, file_path, name=None):
        """从文件导入新的地图集合"""
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        try:
            # 读取导入文件
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        return False, "JSON 格式错误，无法解析文件"
                else:
                    return False, "不支持的文件格式，请使用.json文件"
            
            # 连接数据库
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            
            # 获取导入数据的元数据
            metadata = data.get("metadata", {})
            collection_name = name or metadata.get("name", os.path.basename(file_path))
            collection_desc = metadata.get("description", "导入的美食地图")
            
            # 创建新的地图集合
            cursor.execute("""
                INSERT INTO map_collections (name, description, is_personal, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                collection_name,
                collection_desc,
                0,  # 非个人集合
                datetime.datetime.now().isoformat()
            ))
            
            collection_id = cursor.lastrowid
            
            # 导入美食项
            food_items = data.get("food_items", [])
            successful_imports = 0
            
            for item in food_items:
                try:
                    # 插入美食记录
                    cursor.execute("""
                        INSERT INTO food_items 
                        (collection_id, name, city, rating, reason, address, latitude, longitude, food_type, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        collection_id,
                        item.get("name", "未知店铺"),
                        item.get("city", "未知城市"),
                        float(item.get("rating", 5)),
                        item.get("reason", ""),
                        item.get("address", "未知地址"),
                        float(item.get("latitude", 0)),
                        float(item.get("longitude", 0)),
                        item.get("food_type", "其他"),
                        item.get("created_at", datetime.datetime.now().isoformat())
                    ))
                    
                    food_id = cursor.lastrowid
                    
                    # 处理照片
                    if "photos" in item and item["photos"]:
                        for photo in item["photos"]:
                            try:
                                if isinstance(photo, dict) and "data" in photo:
                                    # 将base64编码的照片数据转换回二进制
                                    photo_data = base64.b64decode(photo["data"])
                                    
                                    cursor.execute("""
                                        INSERT INTO food_photos (food_id, photo_data)
                                        VALUES (?, ?)
                                    """, (food_id, photo_data))
                            except Exception as photo_error:
                                print(f"处理照片时出错: {photo_error}")
                    
                    successful_imports += 1
                    
                except Exception as item_error:
                    print(f"导入食品项时出错: {item_error}")
            
            # 提交事务
            conn.commit()
            
            return True, f"成功导入地图集合 '{collection_name}' 包含 {successful_imports} 条美食记录"
        
        except Exception as e:
            if conn:
                conn.rollback()
            return False, f"导入地图集合时出错: {str(e)}"
        
        finally:
            if conn:
                conn.close()
    
    def delete_collection(self, collection_id):
        """删除指定的地图集合及其所有美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 删除地图集合（由于外键约束，关联的美食记录和照片会自动删除）
            cursor.execute("DELETE FROM map_collections WHERE id = ?", (collection_id,))
            conn.commit()
            
            return True
        
        except Exception as e:
            print(f"Error deleting collection {collection_id}: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if conn:
                conn.close()
    
    def delete_photo(self, photo_id):
        """删除指定的照片"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 删除照片
            cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
            conn.commit()
            
            return True
        
        except Exception as e:
            print(f"Error deleting photo {photo_id}: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if conn:
                conn.close()
    
    def get_photos(self, food_id):
        """获取指定美食项的照片（作为get_photo的别名）"""
        return self.get_photo(food_id)
    
    def add_photo(self, food_id, photo_data):
        """为指定的美食项添加照片"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 插入照片数据
            cursor.execute("""
                INSERT INTO photos (food_item_id, photo_data)
                VALUES (?, ?)
            """, (food_id, photo_data))
            
            conn.commit()
            return cursor.lastrowid
        
        except Exception as e:
            print(f"Error adding photo: {e}")
            if conn:
                conn.rollback()
            return None
        
        finally:
            if conn:
                conn.close() 