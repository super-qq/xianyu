from flask import Flask
from config import DB_CONFIG
import os
from dotenv import load_dotenv

# 加载环境变量（确保能读取到SECRET_KEY）
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # 1. 配置密钥（关键修复：用于会话和flash消息加密）
    # 从环境变量获取，没有则使用临时密钥（生产环境必须设置环境变量）
    app.secret_key = os.getenv('SECRET_KEY', '47656c2675f5a6a21de5af1d6f9f9c7ce8c4edb69321696422013d776ec1384b')
    
    # 2. 其他配置
    app.config['DB_CONFIG'] = DB_CONFIG
    app.config['BASE_IMAGE_DIR'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images')
    
    # 确保图片目录存在
    os.makedirs(app.config['BASE_IMAGE_DIR'], exist_ok=True)
    
    # 注册路由
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
