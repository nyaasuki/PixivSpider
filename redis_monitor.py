import redis

def show_db_status(r, db_index):
    """显示指定数据库的状态信息"""
    try:
        # 切换到指定数据库
        r.select(db_index)
        
        # 检查并显示Cookie状态
        cookie = r.get('cookie')
        if cookie:
            print(f"Cookie值: {cookie}")
        else:
            print("Cookie状态: 匿名")
        
        # 获取所有键
        all_keys = r.keys('*')
        
        # 统计图片ID数量
        pid_count = len([key for key in all_keys if key.startswith('downloaded:') and '_p0' in key])
        print(f"当前存储的图片作品数量: {pid_count}\n")
    except redis.RedisError as e:
        print(f"错误：{str(e)}")

def check_redis_status():
    """检查Redis状态并显示详细信息"""
    try:
        # 连接到Redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 检查连接
        r.ping()
        
        # 获取活跃数据库信息（仅0-5）
        info = r.info()
        keyspace_info = {k: v for k, v in info.items() if k.startswith('db')}
        
        # 过滤0-5范围内的数据库
        valid_indices = set(range(6))  # 0-5
        db_indices = [int(k.replace('db', '')) for k in keyspace_info.keys() if int(k.replace('db', '')) in valid_indices]
        db_indices.sort()
        
        if not db_indices:
            print("\n当前没有活跃的数据库")
            return
        db_list = ', '.join([f"db{i}" for i in db_indices])
        print(f"\n活跃的Redis数据库: {db_list}")
        
        if len(db_indices) == 1:
            # 只有一个数据库，直接显示其信息
            print(f"\n数据库 db{db_indices[0]} 的信息:")
            show_db_status(r, db_indices[0])
        else:
            # 多个数据库，让用户选择
            while True:
                choice = input("\n请选择要查看的数据库编号 (例如: 0 表示db0): ")
                try:
                    db_index = int(choice)
                    if db_index in db_indices:
                        print(f"\n数据库 db{db_index} 的信息:")
                        show_db_status(r, db_index)
                        break
                    else:
                        print("无效的数据库编号，请重试")
                except ValueError:
                    print("请输入有效的数字")
                
    except redis.ConnectionError:
        print("错误：无法连接到Redis服务器，请确保Redis服务正在运行")
    except Exception as e:
        print(f"错误：{str(e)}")

def clear_redis_db():
    """清空Redis数据库"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        # 获取当前数据库信息（仅0-5）
        info = r.info()
        keyspace_info = {k: v for k, v in info.items() if k.startswith('db')}
        
        # 过滤0-5范围内的数据库
        valid_indices = set(range(6))  # 0-5
        db_indices = [int(k.replace('db', '')) for k in keyspace_info.keys() if int(k.replace('db', '')) in valid_indices]
        db_indices.sort()
        
        if not db_indices:
            print("\n当前没有活跃的数据库")
            return
        db_list = ', '.join([f"db{i}" for i in db_indices])
        print(f"\n活跃的Redis数据库: {db_list}")
        print("\n清空选项:")
        print("1. 清空指定数据库")
        print("2. 清空所有数据库")
        print("3. 取消操作")
        
        choice = input("请选择操作 (1-3): ")
        
        if choice == '1':
            if len(db_indices) == 1:
                db_index = db_indices[0]
                confirm = input(f"确定要清空数据库 db{db_index} 吗？(y/n): ")
                if confirm.lower() == 'y':
                    r.select(db_index)
                    r.flushdb()
                    print(f"数据库 db{db_index} 已清空\n")
            else:
                while True:
                    choice = input("\n请选择要清空的数据库编号 (例如: 0 表示db0): ")
                    try:
                        db_index = int(choice)
                        if 0 <= db_index <= 5 and db_index in db_indices:
                            confirm = input(f"确定要清空数据库 db{db_index} 吗？(y/n): ")
                            if confirm.lower() == 'y':
                                r.select(db_index)
                                r.flushdb()
                                print(f"数据库 db{db_index} 已清空\n")
                            break
                        else:
                            print("无效的数据库编号，请重试")
                    except ValueError:
                        print("请输入有效的数字")
                        
        elif choice == '2':
            confirm = input("确定要清空所有数据库吗？(y/n): ")
            if confirm.lower() == 'y':
                for db_index in range(6):  # 0-5
                    r.select(db_index)
                    r.flushdb()
                print("所有的数据库已清空\n")
        elif choice == '3':
            print("已取消操作\n")
        else:
            print("无效的选择\n")
            
    except redis.ConnectionError:
        print("错误：无法连接到Redis服务器，请确保Redis服务正在运行")
    except Exception as e:
        print(f"错误：{str(e)}")

def show_menu():
    """显示交互菜单"""
    while True:
        print("=== Redis管理工具 ===")
        print("1. 显示状态")
        print("2. 清空数据库")
        print("3. 退出")
        choice = input("请选择操作 (1-3): ")
        
        if choice == '1':
            check_redis_status()
        elif choice == '2':
            clear_redis_db()
        elif choice == '3':
            print("退出程序")
            break
        else:
            print("无效的选择，请重试\n")

if __name__ == '__main__':
    show_menu()
