# 美食地图应用 (FTM-FoodTreasureMap)

一个用于记录和可视化美食店铺的桌面应用程序，帮助用户保存、管理和分享自己的美食探索经历。

## 功能特点

- **美食记录管理**：记录美食店铺信息（名称、位置、评分、照片等）
- **地图可视化**：在百度地图上可视化展示美食点位置
- **评分标记系统**：根据评分显示不同颜色的标记，直观区分美食质量
- **探索范围可视化**：显示探索范围（城市视图1km，全国视图10km）
- **多维度筛选**：支持按城市、评分等条件筛选美食点
- **数据导入导出**：支持JSON、CSV格式的数据导入导出，方便数据备份和分享
- **详细信息展示**：支持查看每个美食点的详细信息和推荐理由

## 技术架构

- 前端界面：PyQt5实现美观的用户界面
- 地图服务：基于百度地图API实现地理位置可视化
- 数据存储：使用SQLite数据库本地存储美食数据
- 图片管理：支持美食照片的上传和预览

## 安装与运行

### 环境要求

- Python 3.7+
- PyQt5
- 其他依赖包（详见requirements.txt）

### 安装步骤

1. 克隆仓库到本地

```bash
git clone https://github.com/yourusername/FTM-FoodTreasureMap.git
cd FTM-FoodTreasureMap
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 运行应用

```bash
python main.py
```

## 使用指南

### 添加美食点

1. 点击界面上的"添加"按钮
2. 输入美食店铺信息（名称、地址、评分等）
3. 上传美食照片（可选）
4. 点击"保存"完成添加

### 浏览美食地图

- 切换"城市视图"和"全国视图"查看不同范围的美食点
- 点击地图上的标记查看美食详情
- 使用筛选功能按条件查找特定美食点

### 数据导入导出

- 通过"导出数据"功能将美食数据导出为JSON或CSV格式
- 通过"导入数据"功能从文件中导入其他用户分享的美食点

## 项目结构
