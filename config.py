# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # 加载环境变量

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "12345"),
    "database": os.getenv("DB_NAME", "xianyu"),
    "port": int(os.getenv("DB_PORT", 33326)),
    "charset": "utf8mb4"
}

# 图片基础目录
BASE_IMAGE_DIR = "/Users/lujiaqi/Desktop/xianyu/images/"