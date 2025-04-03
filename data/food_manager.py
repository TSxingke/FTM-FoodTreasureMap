import sqlite3
import json
import os
import datetime
import csv
import base64
import html

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
    
    def export_blog(self, collection_id, file_path):
        """导出地图集合到博客HTML文件"""
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
                        photo_type = "image/jpeg"  # 假设所有图片都是JPEG格式
                        photos.append({
                            "id": photo_id,
                            "data_url": f"data:{photo_type};base64,{photo_base64}"
                        })
                
                item["photos"] = photos
            
            # 读取pointer_1.svg图标内容
            pointer_svg = ""
            try:
                with open("icons/pointer_1.svg", "r", encoding="utf-8") as f:
                    pointer_svg = f.read()
                # 提取SVG内容部分
                if pointer_svg:
                    import re
                    svg_content = re.search(r'<svg.*?</svg>', pointer_svg, re.DOTALL)
                    if svg_content:
                        pointer_svg = svg_content.group(0)
                        # 转换为data URL
                        pointer_svg = "data:image/svg+xml;base64," + base64.b64encode(pointer_svg.encode('utf-8')).decode('utf-8')
            except Exception as e:
                print(f"读取鼠标指针图标失败: {e}")
                # 使用默认图标
                pointer_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23FF5722' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/%3E%3C/svg%3E"
            
            # 生成博客HTML
            html_content = self._generate_blog_html(collection, food_items, pointer_svg)
            
            # 写入HTML文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            return True
        
        except Exception as e:
            print(f"导出博客失败: {e}")
            return False
        
        finally:
            if conn:
                conn.close()
    
    def _generate_blog_html(self, collection, food_items, pointer_svg=None):
        """生成博客HTML内容"""
        # 设置默认鼠标指针
        if not pointer_svg:
            pointer_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23FF5722' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/%3E%3C/svg%3E"
        
        # 对美食项按评分排序
        sorted_items = sorted(food_items, key=lambda x: x["rating"], reverse=True)
        
        # 构建地图标记点的JavaScript代码
        markers_js = ""
        for item in food_items:
            markers_js += f"""
                addFoodMarker(
                    {item["longitude"]}, 
                    {item["latitude"]}, 
                    "{html.escape(item["name"])}", 
                    {item["rating"]}, 
                    {item["id"]}, 
                    "{html.escape(item["address"])}", 
                    "{html.escape(item["reason"] if item["reason"] else "")}", 
                    "{html.escape(item["city"])}", 
                    "{html.escape(item["food_type"])}"
                );
            """
        
        # 构建美食列表的HTML
        food_list_html = ""
        for i, item in enumerate(sorted_items):
            # 计算星级显示
            stars = "★" * int(item["rating"]) + "☆" * (5 - int(item["rating"]))
            half_star = "½" if item["rating"] % 1 >= 0.5 else ""
            
            # 处理照片
            photos_html = ""
            if item["photos"]:
                photos_html += '<div class="food-photos">'
                for photo in item["photos"]:
                    photos_html += f'<img src="{photo["data_url"]}" alt="{html.escape(item["name"])}" class="food-photo" onclick="openLightbox(this.src)">'
                photos_html += '</div>'
            
            food_list_html += f"""
            <div class="food-item" id="food-{item["id"]}">
                <div class="food-header">
                    <h3 class="food-name">{i+1}. {html.escape(item["name"])}</h3>
                    <div class="food-rating">{stars}{half_star} {item["rating"]}</div>
                </div>
                <div class="food-details">
                    <div class="food-meta">
                        <span class="food-type"><i class="food-icon">🍽️</i> {html.escape(item["food_type"])}</span>
                        <span class="food-city"><i class="food-icon">📍</i> {html.escape(item["city"])}</span>
                    </div>
                    <p class="food-address"><i class="food-icon">🏠</i> {html.escape(item["address"])}</p>
                    
                    <div class="food-reason">
                        <h4>推荐理由</h4>
                        <p>{html.escape(item["reason"]) if item["reason"] else "暂无推荐理由"}</p>
                    </div>
                    {photos_html}
                    <button class="locate-btn" onclick="locateOnMap({item["id"]})"><i class="btn-icon">🗺️</i> 在地图上查看</button>
                </div>
            </div>
            """
        
        # 生成完整的HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(collection["name"])} - 美食分享</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <script>
        window.HOST_TYPE = '2';
        window.BMapGL_loadScriptTime = (new Date).getTime();
    </script>
    <script type="text/javascript" src="https://api.map.baidu.com/getscript?type=webgl&v=1.0&ak=OBUkmzeyCj9vCfell3YPGqKGN47Sj9LJ&services=&t=20250313124310"></script>
    <style>
        /* 全局样式 */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary-color: #FF5722;
            --primary-light: #FFCCBC;
            --secondary-color: #2196F3;
            --text-dark: #263238;
            --text-light: #607D8B;
            --background-light: #F5F5F5;
            --card-shadow: 0 4px 20px rgba(0,0,0,0.08);
            --hover-shadow: 0 8px 30px rgba(0,0,0,0.15);
            --transition-main: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }}
        
        body {{
            font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: var(--text-dark);
            background-color: var(--background-light);
            background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23f0f0f0' fill-opacity='0.6'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"),
                            linear-gradient(135deg, #f8f9fa 0%, #f1f2f3 100%);
            background-attachment: fixed;
            position: relative;
        }}
        
        body::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260' viewBox='0 0 260 260'%3E%3Cg fill='%23FF5722' fill-opacity='0.03'%3E%3Cpath d='M24.37 16c.2.65.39 1.32.54 2H21.17l1.17 2.34.45.9-.24.11V28a5 5 0 0 1-2.23 8.94l-.02.06a8 8 0 0 1-7.75 6h-20a8 8 0 0 1-7.74-6l-.02-.06a5 5 0 0 1-2.24-8.94v-6.76l-.79-1.58-.44-.9.9-.44.63-.32H290.43a5 5 0 0 1 3.4 8.9l-.03.01a5 5 0 0 1-3.71 1.62l-.06-.03.4.08a8 8 0 0 1 7.08 7.94v1.8l.96-.39a5 5 0 0 1 6.89 4.62v5.77l-.95.37a7.99 7.99 0 0 1-6.94 8l-.4-.09a5 5 0 0 1-3.95 2.49l-1.64-1.9-20.1 0a5 5 0 0 1-3.8-1.85l-.07-.01a5 5 0 0 1 .19-7.03l.59-.5a7.73 7.73 0 0 1 2.4-.81l-.01-.18c-.3-1.59.89-3.07 2.42-3.48l1.58-.41a4.98 4.98 0 0 1 5.76 2.22c.92 1.49 1.4 3.22 1.4 4.97a8 8 0 0 1-16 0 3.7 3.7 0 0 1-3.7-3.7 3.7 3.7 0 0 1 3.7-3.7 3.69 3.69 0 0 1 3.7 3.7 8 8 0 0 1 16 0c0-1.75-.48-3.48-1.4-4.97a5 5 0 0 1-2.03-1.62 18.63 18.63 0 0 0-8.47-7.19l3.82-.8c4.1 1.4 7.14 4.5 9.13 8.38 1.4-2.46 3.14-4.7 5.27-6.69l.1.09a18.5 18.5 0 0 0-1.12 6.69 5 5 0 0 1 .67.7l-.04.01c.79 1.62 1.03 3.44.67 5.19a7.98 7.98 0 0 1 2.16.85 5 5 0 0 1 7.07.15v.1a5 5 0 0 1-.13 7.07z'/%3E%3C/g%3E%3C/svg%3E");
            z-index: -1;
        }}
        
        .container {{
            max-width: 1300px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 头部样式 */
        header {{
            text-align: center;
            padding: 60px 30px;
            background-color: rgba(255, 255, 255, 0.95);
            box-shadow: var(--card-shadow);
            margin: 20px auto 40px;
            border-radius: 15px;
            position: relative;
            overflow: hidden;
            max-width: 1100px;
        }}
        
        header::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(to right, var(--primary-color), #FF9800);
        }}
        
        header::after {{
            content: "";
            position: absolute;
            top: 6px;
            right: 0;
            bottom: 0;
            width: 200px;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100' fill='%23FF5722' fill-opacity='0.05'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' /%3E%3C/svg%3E");
            background-position: right;
            opacity: 0.3;
            z-index: 0;
        }}
        
        .header-content {{
            position: relative;
            z-index: 1;
        }}
        
        .header-icon {{
            font-size: 2rem;
            color: var(--primary-color);
            margin-bottom: 15px;
            text-shadow: 0 2px 10px rgba(255, 87, 34, 0.2);
        }}
        
        h1 {{
            font-size: 2.8rem;
            color: var(--primary-color);
            margin-bottom: 20px;
            font-weight: 700;
            position: relative;
            display: inline-block;
            letter-spacing: -0.5px;
        }}
        
        h1::after {{
            content: "";
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 3px;
            background: linear-gradient(to right, var(--primary-color), #FF9800);
            border-radius: 3px;
        }}
        
        .description {{
            font-size: 1.2rem;
            color: var(--text-light);
            max-width: 700px;
            margin: 20px auto;
            line-height: 1.8;
        }}
        
        .meta {{
            font-size: 0.95rem;
            color: #888;
            margin-top: 20px;
            display: inline-block;
            padding: 8px 15px;
            background-color: rgba(0,0,0,0.03);
            border-radius: 50px;
        }}
        
        /* 标签页导航 */
        .tabs {{
            display: flex;
            border-bottom: none;
            margin-bottom: 25px;
            justify-content: center;
        }}
        
        .tab {{
            padding: 15px 35px;
            cursor: pointer;
            background-color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
            border-radius: 50px;
            margin: 0 10px;
            box-shadow: var(--card-shadow);
            transition: var(--transition-main);
            color: var(--text-light);
            position: relative;
            overflow: hidden;
            z-index: 1;
            border: 1px solid rgba(0,0,0,0.03);
        }}
        
        .tab::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(to right, var(--primary-light), var(--primary-color));
            opacity: 0;
            z-index: -1;
            transition: var(--transition-main);
        }}
        
        .tab.active {{
            color: white;
            transform: translateY(-3px);
        }}
        
        .tab.active::before {{
            opacity: 1;
        }}
        
        .tab:hover {{
            transform: translateY(-3px);
        }}
        
        /* 内容区域 */
        .tab-content {{
            display: none;
            padding: 35px;
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: var(--card-shadow);
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
        }}
        
        .tab-content::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(to bottom, var(--primary-color), #FF9800);
        }}
        
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.5s ease-in-out;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* 地图容器 */
        #map-container {{
            width: 100%;
            height: 650px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 30px rgba(0,0,0,0.1);
            border: 1px solid rgba(0,0,0,0.05);
        }}
        
        /* 美食列表 */
        .food-list-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 35px;
            padding-bottom: 20px;
            border-bottom: 1px dashed rgba(0,0,0,0.1);
            position: relative;
        }}
        
        .food-list-header::after {{
            content: "美食";
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: #fff;
            padding: 0 15px;
            color: var(--primary-color);
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        .food-list-header h2 {{
            font-size: 1.8rem;
            color: var(--primary-color);
            font-weight: 700;
            position: relative;
            padding-left: 20px;
        }}
        
        .food-list-header h2::before {{
            content: "🍜";
            position: absolute;
            left: -10px;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0.8;
        }}
        
        .food-counter {{
            background-color: rgba(33, 150, 243, 0.1);
            padding: 8px 15px;
            border-radius: 30px;
            font-size: 0.95rem;
            color: var(--secondary-color);
        }}
        
        .food-counter strong {{
            font-weight: 700;
            color: var(--primary-color);
        }}
        
        .food-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 30px;
        }}
        
        .food-item {{
            background: #fff;
            border-radius: 15px;
            box-shadow: var(--card-shadow);
            transition: var(--transition-main);
            overflow: hidden;
            border: 1px solid rgba(0,0,0,0.03);
            height: 100%;
            display: flex;
            flex-direction: column;
            position: relative;
        }}
        
        .food-item:hover {{
            transform: translateY(-5px);
            box-shadow: var(--hover-shadow);
        }}
        
        .food-item::after {{
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 0;
            height: 0;
            border-style: solid;
            border-width: 0 50px 50px 0;
            border-color: transparent rgba(255,87,34,0.05) transparent transparent;
            z-index: 0;
        }}
        
        .food-header {{
            padding: 20px;
            position: relative;
            background: linear-gradient(135deg, #f8f8f8 0%, #ffffff 100%);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }}
        
        .food-header::after {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: var(--primary-color);
        }}
        
        .food-name {{
            font-size: 1.3rem;
            color: var(--text-dark);
            margin: 0;
            padding-left: 12px;
        }}
        
        .food-rating {{
            color: #FF9800;
            font-weight: bold;
            font-size: 1.1rem;
            margin-top: 5px;
            padding-left: 12px;
        }}
        
        .food-details {{
            padding: 20px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .food-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .food-type, .food-city {{
            background: rgba(33, 150, 243, 0.1);
            border-radius: 50px;
            padding: 5px 15px;
            font-size: 0.9rem;
            color: var(--secondary-color);
            display: inline-flex;
            align-items: center;
            margin-right: 10px;
        }}
        
        .food-address {{
            margin: 10px 0;
            color: var(--text-light);
            font-size: 0.95rem;
            display: flex;
            align-items: center;
        }}
        
        .food-icon {{
            margin-right: 8px;
            font-style: normal;
        }}
        
        .food-reason {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 8px;
            border-left: 3px solid var(--primary-color);
            flex-grow: 1;
        }}
        
        .food-reason h4 {{
            margin-bottom: 10px;
            color: var(--primary-color);
            font-size: 1rem;
        }}
        
        .food-reason p {{
            color: var(--text-light);
            font-size: 0.95rem;
            line-height: 1.7;
        }}
        
        .food-photos {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }}
        
        .food-photo {{
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: 8px;
            cursor: pointer;
            transition: var(--transition-main);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .food-photo:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        
        .locate-btn {{
            background: linear-gradient(to right, #4caf50, #3f9142);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: var(--transition-main);
            font-weight: 500;
            align-self: flex-start;
            margin-top: auto;
            display: flex;
            align-items: center;
            box-shadow: 0 3px 10px rgba(76, 175, 80, 0.3);
        }}
        
        .locate-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }}
        
        .btn-icon {{
            margin-right: 8px;
            font-style: normal;
        }}
        
        /* 底部信息 */
        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 40px 20px;
            color: var(--text-light);
            font-size: 0.95rem;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: var(--card-shadow);
            position: relative;
            overflow: hidden;
        }}
        
        footer::before {{
            content: "";
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(to right, var(--primary-color) 0%, transparent 50%, var(--primary-color) 100%);
        }}
        
        footer p {{
            max-width: 700px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}
        
        .footer-icons {{
            display: flex;
            justify-content: center;
            margin-bottom: 15px;
            font-size: 1.5rem;
        }}
        
        .footer-icon {{
            margin: 0 10px;
            color: var(--primary-color);
            opacity: 0.7;
        }}
        
        .share-label {{
            display: block;
            font-size: 1rem;
            margin-top: 5px;
            color: var(--text-dark);
            font-weight: 500;
        }}
        
        /* 灯箱效果 */
        .lightbox {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.85);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 30px;
        }}
        
        .lightbox img {{
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 0 30px rgba(0,0,0,0.5);
        }}
        
        .lightbox.active {{
            display: flex;
        }}
        
        .lightbox-close {{
            position: absolute;
            top: 20px;
            right: 20px;
            color: white;
            font-size: 30px;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }}
        
        /* 响应式设计 */
        @media (max-width: 992px) {{
            .food-list {{
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
            
            .description {{
                font-size: 1rem;
            }}
            
            .tab {{
                padding: 12px 20px;
                font-size: 0.9rem;
            }}
            
            #map-container {{
                height: 450px;
            }}
            
            .food-list {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 480px) {{
            .tabs {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .tab {{
                margin: 0;
                text-align: center;
            }}
            
            .food-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .food-rating {{
                margin-top: 10px;
            }}
            
            .food-meta {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
        
        /* 浮动装饰元素 */
        .floating-icons {{
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            pointer-events: none;
            z-index: -1;
            overflow: hidden;
        }}
        
        .floating-icon {{
            position: absolute;
            opacity: 0.2;
            animation-name: float;
            animation-iteration-count: infinite;
            animation-timing-function: ease-in-out;
        }}
        
        .icon-1 {{
            top: 10%;
            left: 5%;
            font-size: 1.5rem;
            animation-duration: 15s;
        }}
        
        .icon-2 {{
            top: 30%;
            right: 10%;
            font-size: 1.2rem;
            animation-duration: 20s;
            animation-delay: 2s;
        }}
        
        .icon-3 {{
            bottom: 20%;
            left: 15%;
            font-size: 1.3rem;
            animation-duration: 18s;
            animation-delay: 5s;
        }}
        
        .icon-4 {{
            bottom: 35%;
            right: 15%;
            font-size: 1.4rem;
            animation-duration: 22s;
            animation-delay: 8s;
        }}
        
        .icon-5 {{
            top: 60%;
            left: 50%;
            font-size: 1.2rem;
            animation-duration: 25s;
            animation-delay: 1s;
        }}
        
        @keyframes float {{
            0% {{ transform: translate(0, 0) rotate(0deg); }}
            25% {{ transform: translate(15px, 15px) rotate(5deg); }}
            50% {{ transform: translate(0, 20px) rotate(0deg); }}
            75% {{ transform: translate(-15px, 10px) rotate(-5deg); }}
            100% {{ transform: translate(0, 0) rotate(0deg); }}
        }}
        
        /* 页面过渡效果 */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        header, .tabs, .tab-content, footer {{
            animation: fadeIn 0.8s ease-out;
        }}
        
        header {{
            animation-delay: 0.1s;
        }}
        
        .tabs {{
            animation-delay: 0.3s;
        }}
        
        .tab-content {{
            animation-delay: 0.5s;
        }}
        
        footer {{
            animation-delay: 0.7s;
        }}
        
        /* 改进的地图标记悬停效果 */
        .BMapGLOverlay {{
            transition: transform 0.3s ease;
        }}
        
        .BMapGLOverlay:hover {{
            transform: scale(1.2) !important;
            z-index: 100 !important;
        }}
        
        /* 鼠标指针自定义 */
        body {{
            cursor: url("{pointer_svg}"), auto;
        }}
        
        a, button, .tab, .food-photo {{
            cursor: url("{pointer_svg}"), pointer;
        }}
        
        /* 阅读指示器 */
        .progress-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: transparent;
            z-index: 1000;
        }}
        
        .progress-bar {{
            height: 4px;
            background: linear-gradient(to right, var(--primary-color), #FF9800);
            width: 0%;
        }}
        
        /* 自定义滚动条 */
        ::-webkit-scrollbar {{
            width: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(var(--primary-light), var(--primary-color));
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--primary-color);
        }}
    </style>
</head>
<body>
    <div class="progress-container">
        <div class="progress-bar" id="progressBar"></div>
    </div>
    
    <div class="floating-icons">
        <div class="floating-icon icon-1">🍔</div>
        <div class="floating-icon icon-2">🍵</div>
        <div class="floating-icon icon-3">🍦</div>
        <div class="floating-icon icon-4">🍱</div>
        <div class="floating-icon icon-5">🥗</div>
    </div>
    
    <header>
        <div class="header-content">
            <div class="header-icon">🍽️</div>
            <h1>{html.escape(collection["name"])}</h1>
            <p class="description">{html.escape(collection["description"])}</p>
            <p class="meta">创建于: {collection["created_at"].split(".")[0].replace("T", " ")}</p>
        </div>
    </header>
    
    <div class="container">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('map-tab')">地图视图</div>
            <div class="tab" onclick="switchTab('list-tab')">列表视图</div>
        </div>
        
        <div id="map-tab" class="tab-content active">
            <div id="map-container"></div>
        </div>
        
        <div id="list-tab" class="tab-content">
            <div class="food-list-header">
                <h2>美食收藏清单</h2>
                <div class="food-counter">共收录 <strong>{len(food_items)}</strong> 个美食点</div>
            </div>
            <div class="food-list">
                {food_list_html}
            </div>
        </div>
    </div>
    
    <footer>
        <div class="footer-icons">
            <div class="footer-icon">🍕</div>
            <div class="footer-icon">🍜</div>
            <div class="footer-icon">🍣</div>
            <div class="footer-icon">🍰</div>
        </div>
        <span class="share-label">记录味蕾上的小幸福</span>
        <p>由我的美食地图生成 &copy; {datetime.datetime.now().year} | 收集美食记忆，分享舌尖上的幸福</p>
    </footer>
    
    <div class="lightbox" id="lightbox">
        <div class="lightbox-close" onclick="closeLightbox()">×</div>
        <img id="lightbox-img" src="" alt="放大图片">
    </div>

    <script>
        // 初始化地图
        var map;
        var markers = [];
        var infoWindowContent = {{}};
        
        function initMap() {{
            map = new BMapGL.Map("map-container");
            var point = new BMapGL.Point(116.404, 39.915);
            map.centerAndZoom(point, 5);
            
            map.enableScrollWheelZoom();
            map.enableDragging();
            
            map.addControl(new BMapGL.NavigationControl());
            map.addControl(new BMapGL.ScaleControl());
            
            // 添加所有美食标记
            {markers_js}
            
            // 根据标记点自动调整视图
            if (markers.length > 0) {{
                var points = [];
                for (var i = 0; i < markers.length; i++) {{
                    points.push(markers[i].getPosition());
                }}
                
                if (points.length === 1) {{
                    map.centerAndZoom(points[0], 14);
                }} else {{
                    map.setViewport(points);
                }}
            }}
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
            var foodData = {{
                id: id,
                name: name,
                rating: rating,
                address: address,
                reason: reason || "暂无推荐理由",
                city: city,
                food_type: food_type
            }};
            
            // 给marker添加foodData属性
            marker.foodData = foodData;
            
            // 创建信息窗口内容
            var content = `
                <div style="padding: 10px; min-width: 200px;">
                    <h3 style="margin: 0 0 10px 0; font-size: 16px;">${{name}}</h3>
                    <div style="margin-bottom: 8px;">
                        <span style="font-weight: bold;">评分: </span>
                        <span style="color: #ff9800;">${{rating.toFixed(1)}}</span>
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
            
            // 存储信息窗口内容
            infoWindowContent[id] = {{
                content: content,
                point: point
            }};
            
            // 添加点击事件
            marker.addEventListener("click", function() {{
                var info = infoWindowContent[id];
                var infoWindow = new BMapGL.InfoWindow(info.content, {{
                    width: 320,
                    height: 200,
                    title: "",
                    enableMessage: false,
                    enableCloseOnClick: true
                }});
                
                map.infoWindow = infoWindow;
                marker.openInfoWindow(infoWindow, info.point);
                
                // 高亮显示列表中对应的项
                highlightFoodItem(id);
            }});
            
            // 添加到地图
            map.addOverlay(marker);
            markers.push(marker);
            
            // 添加探索范围圆
            var circle = new BMapGL.Circle(point, 1000, {{
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
            if (rating >= 9.0) return "#FF5252"; // 极好
            if (rating >= 8.0) return "#FF7043"; // 很好
            if (rating >= 7.0) return "#FFA726"; // 好
            if (rating >= 6.0) return "#FFCA28"; // 一般
            if (rating >= 5.0) return "#FFEE58"; // 还行
            return "#B0BEC5"; // 差
        }}
        
        // 在地图上定位美食点
        function locateOnMap(id) {{
            var info = infoWindowContent[id];
            if (!info) return;
            
            for (var i = 0; i < markers.length; i++) {{
                if (markers[i].foodData && markers[i].foodData.id == id) {{
                    // 找到匹配的标记
                    var infoWindow = new BMapGL.InfoWindow(info.content, {{
                        width: 320,
                        height: 200,
                        title: "",
                        enableMessage: false,
                        enableCloseOnClick: true
                    }});
                    
                    map.infoWindow = infoWindow;
                    markers[i].openInfoWindow(infoWindow, info.point);
                    
                    // 将地图中心移动到标记位置
                    map.panTo(info.point);
                    
                    // 切换到地图选项卡
                    switchTab('map-tab');
                    
                    break;
                }}
            }}
        }}
        
        // 高亮显示食品项
        function highlightFoodItem(id) {{
            // 移除所有高亮
            var items = document.querySelectorAll('.food-item');
            items.forEach(function(item) {{
                item.style.borderLeft = '';
                item.style.boxShadow = '';
            }});
            
            // 添加高亮
            var targetItem = document.getElementById('food-' + id);
            if (targetItem) {{
                targetItem.style.boxShadow = '0 5px 25px rgba(255, 87, 34, 0.3)';
                targetItem.style.borderLeft = '5px solid #ff5722';
                
                // 如果在列表视图中，滚动到该项
                if (document.getElementById('list-tab').classList.contains('active')) {{
                    targetItem.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }}
        }}
        
        // 切换选项卡
        function switchTab(tabId) {{
            // 隐藏所有选项卡内容
            var contents = document.querySelectorAll('.tab-content');
            contents.forEach(function(content) {{
                content.classList.remove('active');
            }});
            
            // 取消所有选项卡激活状态
            var tabs = document.querySelectorAll('.tab');
            tabs.forEach(function(tab) {{
                tab.classList.remove('active');
            }});
            
            // 激活所选选项卡
            document.getElementById(tabId).classList.add('active');
            
            // 找到所选选项卡对应的导航标签并激活
            var index = tabId === 'map-tab' ? 0 : 1;
            tabs[index].classList.add('active');
        }}
        
        // 照片灯箱功能
        function openLightbox(imgSrc) {{
            var lightbox = document.getElementById('lightbox');
            var lightboxImg = document.getElementById('lightbox-img');
            
            lightboxImg.src = imgSrc;
            lightbox.classList.add('active');
            
            // 阻止滚动
            document.body.style.overflow = 'hidden';
        }}
        
        function closeLightbox() {{
            var lightbox = document.getElementById('lightbox');
            lightbox.classList.remove('active');
            
            // 恢复滚动
            document.body.style.overflow = '';
        }}
        
        // 点击灯箱背景关闭灯箱
        document.getElementById('lightbox').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeLightbox();
            }}
        }});
        
        // 页面加载完成后初始化地图
        window.onload = initMap;
        
        // 阅读进度条
        window.onscroll = function() {{
            var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            var scrolled = (winScroll / height) * 100;
            document.getElementById("progressBar").style.width = scrolled + "%";
        }};
    </script>
</body>
</html>
"""
        
        return html_content 