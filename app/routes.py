from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app  # 新增current_app导入
from .db_operations import insert_pre_product
from .utils import create_product_image_dir
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取表单数据
        summary = request.form.get('summary', '').strip()
        tao_token = request.form.get('tao_token', '').strip()
        price = request.form.get('price', '').strip()
        
        # 简单验证
        errors = []
        if not summary:
            errors.append("商品描述不能为空")
        if not tao_token:
            errors.append("Tao Token不能为空")
        if not price or not price.replace('.', '', 1).isdigit():
            errors.append("请输入有效的价格")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('index.html')
        
        try:
            # 插入数据库
            price_float = float(price)
            product_id = insert_pre_product(summary, tao_token, price_float)
            
            # 创建图片目录 - 使用current_app获取配置（修复错误的核心）
            image_dir = create_product_image_dir(
                base_dir=current_app.config['BASE_IMAGE_DIR'],  # 这里修改为current_app
                product_id=product_id
            )
            
            flash(f"商品录入成功！图片目录：{image_dir}", 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f"操作失败：{str(e)}", 'error')
            return render_template('index.html')
    
    # GET请求显示表单
    return render_template('index.html')
