import time
from login import get_chrome_driver, login
from create_product import create_product, get_pending_products


def main():
    # 1. 获取所有待发布商品
    pending_products = get_pending_products()
    if not pending_products:
        print("没有待发布的商品，程序退出")
        return
    print(f"共发现 {len(pending_products)} 个待发布商品，开始处理...")
    
    # 2. 创建浏览器驱动
    driver = get_chrome_driver()
    
    try:
        # 3. 登录系统
        if not login(driver):
            print("登录失败，程序退出")
            return
            
        # 4. 等待页面加载完成
        time.sleep(3)
        
        # 5. 循环处理每个待发布商品
        for pre_product in pending_products:
            print(f"\n===== 开始处理商品 ID: {pre_product['id']} =====")
            create_product(driver, pre_product)
            time.sleep(5)  # 每个商品处理间隔，避免操作过快
            
        # 6. 保持浏览器打开，方便查看结果
        input("所有商品处理完毕，按回车键关闭浏览器...")
        
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        
    finally:
        # 关闭浏览器
        driver.quit()


if __name__ == "__main__":
    main()