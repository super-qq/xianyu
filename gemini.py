import google.generativeai as genai
import os
from pathlib import Path
from typing import List, Optional, Tuple


genai.configure(api_key="AIzaSyBGpWdLkQJeGr9WmQ9qsscX_ERMh4_xMx8")

# 支持的图片格式
SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')

def get_image_files_from_dir(directory: str) -> List[str]:
    """获取目录中所有支持的图片文件路径"""
    image_paths = []
    if not os.path.isdir(directory):
        print(f"错误：目录不存在 - {directory}")
        return image_paths
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            image_paths.append(file_path)
    
    print(f"在目录 '{directory}' 中找到 {len(image_paths)} 张图片")
    return image_paths

def load_images(image_paths: List[str]) -> Optional[List[dict]]:
    """加载多张图片并转换为Gemini可接受的格式"""
    images_content = []
    
    for image_path in image_paths:
        try:
            if not Path(image_path).exists():
                print(f"跳过：图片不存在 - {image_path}")
                continue
            
            image_data = Path(image_path).read_bytes()
            
            # 确定MIME类型
            if image_path.lower().endswith(('.jpg', '.jpeg')):
                mime_type = "image/jpeg"
            elif image_path.lower().endswith('.png'):
                mime_type = "image/png"
            elif image_path.lower().endswith('.webp'):
                mime_type = "image/webp"
            else:
                print(f"跳过：不支持的图片格式 - {image_path}")
                continue
            
            images_content.append({"mime_type": mime_type, "data": image_data})
            
        except Exception as e:
            print(f"加载图片失败 {image_path}：{str(e)}")
    
    return images_content if images_content else None

def parse_generated_content(generated_text: str) -> Tuple[Optional[str], Optional[str]]:
    """解析生成的内容，提取标题和描述"""
    if not generated_text:
        return None, None
        
    # 分割标题和正文
    lines = [line.strip() for line in generated_text.split('\n') if line.strip()]
    if not lines:
        return None, None
        
    title = lines[0]
    description = '\n'.join(lines[1:])
    
    return title, description

# gemini.py（修改generate_product_info函数）
def generate_product_info(image_dir: str, summary: str) -> Tuple[Optional[str], Optional[str]]:
    """生成商品标题和描述并返回（新增summary参数）"""
    # 获取图片路径
    image_paths = get_image_files_from_dir(image_dir)
    if not image_paths:
        print("没有找到可处理的图片")
        return None, None
    
    # 加载所有图片
    print("正在加载图片...")
    images_content = load_images(image_paths)
    if not images_content:
        print("没有成功加载任何图片")
        return None, None
    
    # 闲鱼平台商品文案生成提示词（结合传入的summary）
    prompt = f"""
    请分析我提供的所有商品图片和基础描述，为我生成一段适合在闲鱼平台发布的商品文案，要求直接返回标题和文案，无需返回其他内容。
    请遵循以下规则：
    1. 文案中，不要出现**标题或**文案等直接标识标题和文案的输出。“”
    2. 文案中，不要出现图标例如🔥、🚽
    商品基础描述：{summary}
    
    要求如下：
    1. 首先给出一个吸引人的商品标题，不超过20个字
    2. 然后按照以下结构生成详情：
        突出商品最核心的2-3个卖点，语言简洁有力
       【说明】：详细介绍商品材质、功能或使用场景，让买家了解商品价值
       【规格】：说明商品的尺寸、重量、颜色、数量等具体信息
       【发货】：说明发货时间、快递方式、包邮情况等物流信息
       【备注】：补充其他重要信息，如新旧程度、生产日期、特别提醒等
    3. 最后添加一句友好的结尾，例如："拍下即可发货，想了解更多可以私聊我哦～"
    4. 整体语气要亲切自然，符合个人卖家的口吻，避免过于官方或生硬的表达
    5. 所有内容要基于图片中的商品实际情况和基础描述，不要虚构不存在的信息
    """
    
    # 初始化模型（其余代码不变）
    model = genai.GenerativeModel(
        model_name="models/gemini-2.0-flash-lite",
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 1000,
            "top_p": 0.9,
        }
    )
    
    try:
        response = model.generate_content([prompt] + images_content)
        response.resolve()
        
        # 检查安全过滤（其余代码不变）
        if response.candidates:
            for candidate in response.candidates:
                if candidate.finish_reason == "SAFETY":
                    print("生成失败：内容触发安全过滤")
                    return None, None
        
        return parse_generated_content(response.text)
        
    except Exception as e:
        print(f"模型调用失败：{str(e)}")
        return None, None