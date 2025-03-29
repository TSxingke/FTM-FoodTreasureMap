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
            
            # 生成博客HTML
            html_content = self._generate_blog_html(collection, food_items)
            
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
    
    def _generate_blog_html(self, collection, food_items):
        """生成博客HTML内容"""
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
                    photos_html += f'<img src="{photo["data_url"]}" alt="{html.escape(item["name"])}" class="food-photo">'
                photos_html += '</div>'
            
            food_list_html += f"""
            <div class="food-item" id="food-{item["id"]}">
                <div class="food-header">
                    <h3 class="food-name">{i+1}. {html.escape(item["name"])}</h3>
                    <div class="food-rating">{stars}{half_star} {item["rating"]}</div>
                </div>
                <div class="food-details">
                    <p><span class="label">类型:</span> {html.escape(item["food_type"])}</p>
                    <p><span class="label">地址:</span> {html.escape(item["address"])}</p>
                    <p><span class="label">城市:</span> {html.escape(item["city"])}</p>
                    <div class="food-reason">
                        <p class="label">推荐理由:</p>
                        <p>{html.escape(item["reason"]) if item["reason"] else "暂无推荐理由"}</p>
                    </div>
                    {photos_html}
                    <button class="locate-btn" onclick="locateOnMap({item["id"]})">在地图上查看</button>
                </div>
            </div>
            """
        
        # 生成完整的HTML - 修改变量名为html_content而不是html
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(collection["name"])} - 美食分享</title>
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
        
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 头部样式 */
        header {{
            text-align: center;
            padding: 30px 0;
            background-color: #fff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        h1 {{
            font-size: 28px;
            color: #d32f2f;
            margin-bottom: 10px;
        }}
        
        .description {{
            font-size: 16px;
            color: #666;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        /* 标签页导航 */
        .tabs {{
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
        }}
        
        .tab {{
            padding: 10px 20px;
            cursor: pointer;
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }}
        
        .tab.active {{
            background-color: #fff;
            border-bottom: 1px solid #fff;
            margin-bottom: -1px;
            font-weight: bold;
        }}
        
        /* 内容区域 */
        .tab-content {{
            display: none;
            padding: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        /* 地图容器 */
        #map-container {{
            width: 100%;
            height: 600px;
            border-radius: 5px;
            overflow: hidden;
        }}
        
        /* 美食列表 */
        .food-list {{
            margin-top: 20px;
        }}
        
        .food-item {{
            background: #fff;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            overflow: hidden;
        }}
        
        .food-item:hover {{
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .food-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background-color: #f8f8f8;
            border-bottom: 1px solid #eee;
        }}
        
        .food-name {{
            font-size: 18px;
            color: #333;
            margin: 0;
        }}
        
        .food-rating {{
            color: #ff9800;
            font-weight: bold;
        }}
        
        .food-details {{
            padding: 20px;
        }}
        
        .label {{
            font-weight: bold;
            color: #555;
        }}
        
        .food-reason {{
            margin: 15px 0;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        
        .food-photos {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }}
        
        .food-photo {{
            width: 150px;
            height: 150px;
            object-fit: cover;
            border-radius: 5px;
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        
        .food-photo:hover {{
            transform: scale(1.05);
        }}
        
        .locate-btn {{
            background-color: #4caf50;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }}
        
        .locate-btn:hover {{
            background-color: #45a049;
        }}
        
        /* 底部信息 */
        footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #777;
            font-size: 14px;
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            #map-container {{
                height: 400px;
            }}
            
            .food-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .food-rating {{
                margin-top: 5px;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{html.escape(collection["name"])}</h1>
        <p class="description">{html.escape(collection["description"])}</p>
        <p class="meta">创建于: {collection["created_at"].split(".")[0].replace("T", " ")}</p>
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
            <h2>共收录 {len(food_items)} 个美食点</h2>
            <div class="food-list">
                {food_list_html}
            </div>
        </div>
    </div>
    
    <footer>
        <p>由我的美食地图生成 &copy; {datetime.datetime.now().year}</p>
    </footer>

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
                var info = infoWindowContent[foodData.id];
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
                highlightFoodItem(foodData.id);
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
            for (var i = 0; i < markers.length; i++) {{
                if (markers[i].foodData && markers[i].foodData.id == id) {{
                    // 找到匹配的标记
                    var info = infoWindowContent[id];
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
            }});
            
            // 添加高亮
            var targetItem = document.getElementById('food-' + id);
            if (targetItem) {{
                targetItem.style.borderLeft = '5px solid #ff5252';
                
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
        
        // 页面加载完成后初始化地图
        window.onload = initMap;
    </script>
</body>
</html>
"""
        
        return html_content 