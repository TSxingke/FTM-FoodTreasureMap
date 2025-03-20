import sqlite3
import json
import os
import datetime
import csv

class FoodManager:
    def __init__(self, db_path="data/food_map.db"):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def add_food_item(self, food_data):
        """添加新的美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 插入美食记录
            cursor.execute("""
                INSERT INTO food_items 
                (name, city, rating, reason, address, latitude, longitude, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                food_data["name"],
                food_data["city"],
                food_data["rating"],
                food_data["reason"],
                food_data["address"],
                food_data["latitude"],
                food_data["longitude"],
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
                       latitude, longitude, created_at
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
        """删除美食记录"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 删除美食记录（由于外键约束，相关的照片会自动删除）
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
            
            # 更新美食记录
            cursor.execute("""
                UPDATE food_items 
                SET name = ?, city = ?, rating = ?, reason = ?, 
                    address = ?, latitude = ?, longitude = ?
                WHERE id = ?
            """, (
                food_data["name"],
                food_data["city"],
                food_data["rating"],
                food_data["reason"],
                food_data["address"],
                food_data["latitude"],
                food_data["longitude"],
                food_id
            ))
            
            # 如果有新照片，添加照片
            if "photos" in food_data and food_data["photos"]:
                # 可选：先删除旧照片
                # cursor.execute("DELETE FROM food_photos WHERE food_id = ?", (food_id,))
                
                # 添加新照片
                for photo_data in food_data["photos"]:
                    cursor.execute("""
                        INSERT INTO food_photos (food_id, photo_data)
                        VALUES (?, ?)
                    """, (food_id, photo_data))
            
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
                       latitude, longitude, created_at
                FROM food_items
                ORDER BY created_at DESC
            """)
            
            food_items = []
            for row in cursor.fetchall():
                food_item = dict(row)
                
                # 不导出照片数据，太大了
                food_item["has_photos"] = False
                
                # 检查是否有照片
                cursor.execute("""
                    SELECT COUNT(*) FROM food_photos
                    WHERE food_id = ?
                """, (food_item["id"],))
                
                count = cursor.fetchone()[0]
                if count > 0:
                    food_item["has_photos"] = True
                
                food_items.append(food_item)
            
            # 根据文件扩展名选择导出格式
            if file_path.endswith(".json"):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(food_items, f, ensure_ascii=False, indent=2)
            
            elif file_path.endswith(".csv"):
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    if food_items:
                        # 获取字段名
                        fieldnames = food_items[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(food_items)
            
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
    
    def get_user_food_items(self):
        """获取用户自己的美食数据（非导入的）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM food_items WHERE is_imported = 0 OR is_imported IS NULL"
        cursor.execute(query)
        
        items = []
        for row in cursor.fetchall():
            item = dict(row)
            items.append(item)
        
        conn.close()
        return items
    
    def get_imported_food_items(self):
        """获取导入的美食数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM food_items WHERE is_imported = 1"
        cursor.execute(query)
        
        items = []
        for row in cursor.fetchall():
            item = dict(row)
            items.append(item)
        
        conn.close()
        return items 