from PIL import Image, ImageDraw
import os

def create_star_icon(filename, color):
    """创建星形图标"""
    size = 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制五角星
    outer_radius = size // 2 - 2
    inner_radius = outer_radius // 2
    center = size // 2
    
    points = []
    for i in range(10):
        # 交替使用外半径和内半径
        radius = outer_radius if i % 2 == 0 else inner_radius
        angle = i * 36 * 3.14159 / 180
        # 简化计算，避免过长表达式
        x = center + radius * 0.9 * (0.9 if i % 2 == 0 else 1)
        y = center - radius * 0.9 * (0.9 if i % 2 == 0 else 1)
        
        if i == 0:
            # 第一个点在顶部
            x = center
            y = center - outer_radius
        elif i == 1:
            # 第二个点在右上
            x = center + inner_radius * 0.9
            y = center - inner_radius * 0.9
        elif i == 2:
            # 第三个点在右侧
            x = center + outer_radius
            y = center
        elif i == 3:
            # 第四个点在右下
            x = center + inner_radius * 0.9
            y = center + inner_radius * 0.9
        elif i == 4:
            # 第五个点在底部
            x = center
            y = center + outer_radius
        elif i == 5:
            # 第六个点在左下
            x = center - inner_radius * 0.9
            y = center + inner_radius * 0.9
        elif i == 6:
            # 第七个点在左侧
            x = center - outer_radius
            y = center
        elif i == 7:
            # 第八个点在左上
            x = center - inner_radius * 0.9
            y = center - inner_radius * 0.9
        elif i == 8:
            # 回到顶部
            x = center
            y = center - outer_radius
        
        points.append((x, y))
    
    # 绘制五角星
    draw.polygon(points, fill=color)
    
    # 保存图标
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)

def create_action_icon(filename, color, shape):
    """创建操作图标"""
    size = 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    padding = 4
    
    if shape == "add":
        # 绘制加号
        draw.rectangle([padding, size//2-2, size-padding, size//2+2], fill=color)
        draw.rectangle([size//2-2, padding, size//2+2, size-padding], fill=color)
    
    elif shape == "export":
        # 绘制导出图标（向下箭头）
        points = [
            (size//2, size-padding),  # 底部中心
            (size//2-6, size-padding-8),  # 左下
            (size//2-3, size-padding-8),  # 左下内
            (size//2-3, padding+4),  # 左上
            (size//2+3, padding+4),  # 右上
            (size//2+3, size-padding-8),  # 右下内
            (size//2+6, size-padding-8),  # 右下
        ]
        draw.polygon(points, fill=color)
        # 绘制顶部横线
        draw.rectangle([size//2-8, padding, size//2+8, padding+3], fill=color)
    
    elif shape == "exit":
        # 绘制退出图标（X）
        draw.line([(padding, padding), (size-padding, size-padding)], fill=color, width=3)
        draw.line([(padding, size-padding), (size-padding, padding)], fill=color, width=3)
    
    # 保存图标
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename)

def main():
    """创建所有需要的图标"""
    # 创建星级图标
    create_star_icon("icons/star_gold.png", "#FFD700")  # 金色
    create_star_icon("icons/star_silver.png", "#C0C0C0")  # 银色
    create_star_icon("icons/star_bronze.png", "#CD7F32")  # 铜色
    
    # 创建操作图标
    create_action_icon("icons/add.png", "#32CD32", "add")  # 绿色加号
    create_action_icon("icons/export.png", "#1E90FF", "export")  # 蓝色导出
    create_action_icon("icons/exit.png", "#FF4500", "exit")  # 红色退出

if __name__ == "__main__":
    main()