import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from gemini import generate_product_info
import pymysql
from datetime import datetime, timedelta
from config import DB_CONFIG, BASE_IMAGE_DIR


# 数据库连接工具函数
def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor
    )

# 获取所有待发布的商品
def get_pending_products():
    """获取所有待发布商品（is_release=0）"""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT id, summary, price, tao_token, product_id FROM pre_product WHERE is_release = 0"
            cursor.execute(sql)
            return cursor.fetchall()  # 返回字典列表
    except Exception as e:
        print(f"查询待发布商品失败：{str(e)}")
        return []
    finally:
        if connection:
            connection.close()

# 同步已发布商品信息到product表
def sync_to_product_table(pre_id, title, summary, price, tao_token):
    """将发布成功的商品信息同步到product表"""
    connection = None
    try:
        connection = get_db_connection()
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 计算7天后的时间
        deleted_time = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        
        with connection.cursor() as cursor:
            # 插入product表
            sql = """
            INSERT INTO product (title, summary, price, tao_token, created_time, deleted_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (title, summary, price, tao_token, created_time, deleted_time))
            
            # 更新pre_product表的发布状态
            update_sql = "UPDATE pre_product SET is_release = 1 WHERE id = %s"
            cursor.execute(update_sql, (pre_id,))
            
            connection.commit()
            print(f"商品 {pre_id} 已成功同步到product表")
            return True
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"同步商品信息失败：{str(e)}")
        return False
    finally:
        if connection:
            connection.close()




def navigate_to_product_creation(driver):
    """导航到商品发布页面"""
    try:
        # 点击销售管理-商品
        product_menu = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='app']/section/section/aside/div/div[1]/ul/li[1]/ul/div[3]/li/span")))
        product_menu.click()
        
        time.sleep(2)

        # 点击新建商品
        new_product_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[2]/div[1]/button[6]")))
        new_product_btn.click()
        print("已进入商品发布界面")
        return True
        
    except Exception as e:
        print(f"导航到商品发布页面失败: {str(e)}")
        return False


def fill_product_basic_info(driver):
    """填写商品基本信息"""
    try:
        time.sleep(2) 
        # 选择商品类型
        product_type = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[1]/div[2]/div/div[2]/label[1]/span[1]/span")))
        product_type.click()
        print("商品类型已选择：普通商品")
        time.sleep(2) 
        
        # 选择商品分类
        categories_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[1]/div[3]/div/div/div[1]/input"))  
        )
        categories_input.clear()  
        categories_input.send_keys("厨房纸巾") 
        time.sleep(2) 

        categories_selected = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[1]/div[3]/div/div/div[2]/div/div[1]/div/div")))
        categories_selected.click()
        print("商品分类已选择：厨房纸巾")

        time.sleep(2) 

        # 选择品牌
        brand_other = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[1]/div[4]/div/div/div[1]")))
        brand_other.click()
        print("商品属性已选择：other/其他")

        time.sleep(2)

        # 定位判断勾选状态的元素
        status_element_xpath = '//*[@id="app"]/section/section/main/div/div/div[1]/div/form/div[2]/div[2]/div/ul/li[1]/div[2]/div'
        status_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, status_element_xpath))
        )
        # 获取元素的class属性
        element_class = status_element.get_attribute('class')

        # 定位店铺选择的点击元素（假设是li元素，可根据实际情况调整）
        shop_element = driver.find_element(By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[2]/div[2]/div/ul/li[1]")
        
        # 判断状态：未勾选（un-selected-icon）则点击，已勾选（select-icon）则不处理
        if 'un-selected-icon' in element_class:
            shop_element.click()
            print("店铺未勾选，执行点击操作")
        else:
            print("店铺已勾选，不执行操作")


        return True
        
    except Exception as e:
        print(f"商品基本信息填写错误: {str(e)}")
        return False


def upload_product_images(driver, image_dir):
    """上传商品图片（核心逻辑：定位file输入框 + 传入多图片路径）"""
    try:


        # 2. 定位隐藏的file输入框（Selenium只能通过type="file"的输入框上传文件）
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[1]/div[2]/form/div/div[1]/div/div[1]/div/div/div/input"))  # 需根据实际页面调整XPath
        )

        # 3. 收集图片路径（只处理png/jpg/jpeg/webp格式）
        image_paths = []
        for filename in os.listdir(image_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                image_paths.append(os.path.join(image_dir, filename))
        
        if not image_paths:
            print("警告：图片目录中没有可上传的图片！")
            return False

        # 4. 多图片路径用\n拼接，传给file输入框（Selenium支持这种方式批量上传）
        files_to_upload = "\n".join(image_paths)
        file_input.send_keys(files_to_upload)
        print(f"已选择 {len(image_paths)} 张图片准备上传")

        # 5. 等待图片上传完成（需根据页面“上传成功的预览图”调整定位）
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[1]/div[2]/form/div/div[1]/div/div[1]/div/div[1]/div[1]"))  # 需根据实际页面调整XPath
        )
        print("图片上传完成")
        return True

    except Exception as e:
        print(f"图片上传失败: {str(e)}")
        return False


# 选择发货区域
def select_shipping_area(driver):
    """选择发货区域为：浙江省金华市义乌市"""
    try:
        # 1. 定位发货地输入框，等待元素可见
        shipping_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[1]/div[2]/form/div/div[4]/div/div/div/div[1]/input"))
        )
        # 2. 获取输入框当前值（通过value属性，符合大部分输入框组件逻辑）
        current_shipping = shipping_input.get_attribute("value").strip()
        # 3. 判断是否已为目标地址，是则直接返回
        if current_shipping == "浙江省金华市义乌市":
            print("✅ 发货地已填写为目标地址，跳过选择流程")
            return True

        shipping_area = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[1]/div[2]/form/div/div[4]/div/div/div/div[1]/input")))
        shipping_area.click()
        print("发货地已选择，即将弹窗！！！")
        time.sleep(2)
        # 1. 等待“请选择发货区域”弹窗出现
        shipping_modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[1]/div[2]/form/div/div[4]/div/div/div/div[1]/input"))
        )
        print("✅ 发货区域弹窗已加载")

        # 2. 选择“省”为浙江省
        province_select = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[2]/div[1]/div/div[2]/div[1]/div[2]/div/input"))
        )
        province_select.click()
        zhejiang_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[1]/div[1]/ul/li[11]"))
        )
        zhejiang_option.click()
        print("✅ 已选择：浙江省")
        time.sleep(1)  # 等待下拉框收起

        # 3. 选择“市”为金华市
        city_select = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[2]/div[1]/div/div[2]/div[1]/div[3]/div[1]/input"))
        )
        city_select.click()
        jinhua_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div[1]/div[1]/ul/li[7]"))
        )
        jinhua_option.click()
        print("✅ 已选择：金华市")
        time.sleep(1)

        # 4. 选择“区”为义乌市
        district_select = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[2]/div[1]/div/div[2]/div[1]/div[4]/div[1]/input"))
        )
        district_select.click()
        yiwu_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[5]/div[1]/div[1]/ul/li[8]"))
        )
        yiwu_option.click()
        print("✅ 已选择：义乌市")
        time.sleep(1)

        # 5. 点击“确认选择”按钮
        confirm_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[2]/div[1]/div/div[2]/div[2]/button[2]"))
        )
        confirm_btn.click()
        print("✅ 已确认发货区域")
        return True
    except Exception as e:
        print(f"❌ 选择发货区域失败：{str(e)}")
        return False


# 修改fill_product_details函数，接收生成的title和description
def fill_product_details(driver, image_dir, title, description):
    """填写商品详情（直接使用传入的标题和描述）"""
    try:
        print(f"使用生成的标题: {title}")
        
        # 填写商品标题
        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[1]/div[2]/form/div/div[2]/div/div[1]/input"))
        )
        title_input.clear()
        title_input.send_keys(title)
        print("已填写商品标题")
        
        # 填写商品详情
        detail_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[4]/div[1]/div[2]/form/div/div[3]/div/div[1]/textarea"))
        )
        detail_input.clear()
        detail_input.send_keys(description)
        print("已填写商品详情")
        
        return True
        
    except Exception as e:
        print(f"商品详情填写错误: {str(e)}")
        return False





# 修改fill_price_inventory函数，接收price参数
def fill_price_inventory(driver, price):
    """填写价格库存并点击发布商品（使用传入的price）"""
    try:
        # ---------- 1. 填写原价，再目前单价的基础上增加20% ----------
        price_float = float(price)
        original_price = round(round(price_float * 1.25, 2))  # 增加25%并四舍五入保留2位
        original_price_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[5]/div[3]/div/div/input")
            )
        )
        original_price_input.clear()
        original_price_input.send_keys(str(original_price))  # 原价可根据需求调整
        print(f"✅ 已填写原价为 ¥{original_price}（售价的125%）")

        # 填写售价（使用传入的price）
        price_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[5]/div[4]/div/div/div/input")
            )
        )
        price_input.clear()
        price_input.send_keys(str(price))  # 确保是字符串类型
        print(f"✅ 已填写售价为 ¥{price}")

        # 库存固定填10
        stock_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[1]/div/form/div[5]/div[5]/div/div/div/input")
            )
        )
        stock_input.clear()
        stock_input.send_keys("10")
        print("✅ 已填写库存为 10")

        # 点击发布按钮（如果需要自动发布，取消注释下面的代码）
        confirm_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='app']/section/section/main/div/div/div[2]/div[2]/div/button")
            )
        )
        confirm_btn.click()
        print("✅ 已点击发布按钮，商品正在提交中...")
        return True

    except Exception as e:
        print(f"❌ 填写价格库存或发布商品失败：{str(e)}")
        return False




# 修改create_product函数，接收pre_product的信息
def create_product(driver, pre_product):
    """完整的商品创建流程（接收pre_product字典参数）"""
    pre_id = pre_product["id"]
    summary = pre_product["summary"]
    price = pre_product["price"]
    tao_token = pre_product["tao_token"]
    
    # 动态生成图片目录
    image_dir = os.path.join(BASE_IMAGE_DIR, str(pre_id))
    print(f"开始处理商品 {pre_id}，图片目录：{image_dir}")

    try:
        if not navigate_to_product_creation(driver):
            raise Exception("导航到商品发布页面失败")
            
        if not fill_product_basic_info(driver):
            raise Exception("填写商品基本信息失败")
            
        if not upload_product_images(driver, image_dir):
            print("图片上传失败，继续执行其他步骤...")

        # 调用Gemini生成文案（传入summary）
        title, description = generate_product_info(image_dir, summary)
        if not title or not description:
            raise Exception("生成商品文案失败")
        
        if not fill_product_details(driver, image_dir, title, description):  # 注意这里需要修改fill_product_details
            raise Exception("填写商品详情失败")
        
        if not select_shipping_area(driver):
            raise Exception("选择发货区域失败")
        
        if not fill_price_inventory(driver, price):  # 传入price
            raise Exception("填写价格库存失败")
        
        # 同步到product表
        if not sync_to_product_table(pre_id, title, description, price, tao_token):
            raise Exception("同步商品信息到product表失败")
        
        print(f"商品 {pre_id} 发布流程完成")
        return True
    except Exception as e:
        print(f"商品 {pre_id} 处理失败：{str(e)}")
        return False