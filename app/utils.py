import os

def create_product_image_dir(base_dir, product_id):
    """创建商品图片目录"""
    dir_path = os.path.join(base_dir, str(product_id))
    os.makedirs(dir_path, exist_ok=True)
    return dir_path
