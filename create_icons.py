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
    """检查所需的图标是否存在，并列出图标清单"""
    # 列出需要的图标及其用途
    required_icons = {
        "icons/star_gold.png": "显示餐厅的金级评分",
        "icons/star_silver.png": "显示餐厅的银级评分",
        "icons/star_bronze.png": "显示餐厅的铜级评分",
        "icons/add.png": "添加新的美食记录按钮",
        "icons/export.png": "导出数据按钮",
        "icons/exit.png": "退出应用按钮",
        "icons/import.png": "导入数据按钮", 
        "icons/key.png": "设置API密钥按钮"
    }
    
    # 检查是否所有图标都存在
    missing_icons = []
    for icon_path in required_icons:
        if not os.path.exists(icon_path):
            missing_icons.append(icon_path)
    
    # 如果有缺失的图标，显示提示信息
    if missing_icons:
        print("以下图标文件缺失，请确保它们存在于正确的位置:")
        for icon in missing_icons:
            print(f"- {icon}: {required_icons[icon]}")
        print("\n请注意：应用程序需要这些图标才能正常显示。请手动添加这些图标到对应位置。")
    
    return missing_icons

if __name__ == "__main__":
    main()