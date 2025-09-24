from app import create_app

app = create_app()

if __name__ == '__main__':
    # 调试模式开启（生产环境需关闭）
    app.run(debug=True, host='0.0.0.0', port=30055)
