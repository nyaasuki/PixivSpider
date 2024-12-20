#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Pixiv import PixivSpider
import redis_monitor
import sys

def show_main_menu():
    """显示主菜单并处理用户选择"""
    while True:
        print("\n=== PixivSpider ===")
        print("1. 爬取每日排行榜")
        print("2. Redis数据库操作")
        print("3. 退出程序")
        
        try:
            choice = input("\n请选择操作 (1-3): ")
            
            if choice == "1":
                print("\n=== 启动PixivSpider ===")
                print("确保已安装并启动Redis服务")
                print("确保已准备好有效的Pixiv Cookie")
                try:
                    PixivSpider.pixiv_main()
                except redis.exceptions.ConnectionError:
                    print('错误：无法连接到Redis服务，请确保Redis服务正在运行')
                except KeyboardInterrupt:
                    print('\n用户中断运行')
                except Exception as e:
                    print(f'发生错误：{str(e)}')
                    
            elif choice == "2":
                print("\n=== 启动Redis管理工具 ===")
                redis_monitor.show_menu()
                
            elif choice == "3":
                print("\nbye!")
                sys.exit(0)
                
            else:
                print("\n无效的选择，请重试")
                
        except KeyboardInterrupt:
            print("\n\n检测到Ctrl+C，正在安全退出...")
            sys.exit(0)
        except Exception as e:
            print(f"\n发生错误：{str(e)}")

if __name__ == "__main__":
    try:
        import redis
        import requests
    except ImportError:
        print('检测到缺少必要包！正在尝试安装！.....')
        import os
        os.system(r'pip install -r requirements.txt')
        import redis
        import requests
        
    
    show_main_menu()
