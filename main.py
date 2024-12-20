#!/usr/bin/env python3
"""
Pixiv爬虫 - 主程序入口
环境需求：Python3.8+ / Redis 
"""
import sys
from typing import NoReturn
import requests.packages.urllib3
from rich.console import Console
import redis.exceptions

from pixiv_spider import PixivSpider
import redis_monitor
from config import REDIS_CONFIG

# 禁用SSL警告
requests.packages.urllib3.disable_warnings()

console = Console()

def show_main_menu() -> NoReturn:
    """显示主菜单并处理用户选择"""
    while True:
        try:
            console.print("\n=== PixivSpider ===")
            console.print("1. 爬取每日排行榜")
            console.print("2. Redis数据库操作")
            console.print("3. 退出程序")
            
            choice = console.input("\n请选择操作 (1-3): ")
            
            if choice == "1":
                run_spider()
            elif choice == "2":
                run_redis_monitor()
            elif choice == "3":
                console.print("\n[green]再见![/green]")
                sys.exit(0)
            else:
                console.print("\n[red]无效的选择，请重试[/red]")
                
        except KeyboardInterrupt:
            console.print("\n\n[yellow]检测到Ctrl+C，正在安全退出...[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"\n[red]发生错误：{str(e)}[/red]")

def run_spider() -> None:
    """运行Pixiv爬虫"""
    console.print("\n=== 启动PixivSpider ===")
    console.print("[yellow]确保已安装并启动Redis服务[/yellow]")
    console.print("[yellow]确保已准备好有效的Pixiv Cookie[/yellow]")
    
    while True:
        try:
            console.print("\n[cyan]可用的Redis数据库:[/cyan]")
            min_db, max_db = REDIS_CONFIG.db_range
            for i in range(min_db, max_db + 1):
                console.print(f"{i}.DB{i}")
                
            db_choice = console.input("\n请选择Redis数据库: ")
            db_num = int(db_choice)
            
            if min_db <= db_num <= max_db:
                spider = PixivSpider(db_num)
                spider.run()
                break
            else:
                console.print(f"[red]错误：请输入{min_db}到{max_db}之间的数字[/red]")
                
        except redis.exceptions.ConnectionError:
            console.print('[red]错误：无法连接到Redis服务，请确保Redis服务正在运行[/red]')
            break
        except ValueError:
            console.print("[red]错误：请输入有效的数字[/red]")
        except KeyboardInterrupt:
            console.print('\n[yellow]用户中断运行[/yellow]')
            break
        except Exception as e:
            console.print(f'[red]发生错误：{str(e)}[/red]')
            break

def run_redis_monitor() -> None:
    """运行Redis管理工具"""
    console.print("\n=== 启动Redis管理工具 ===")
    redis_monitor.show_menu()

def check_dependencies() -> None:
    """检查并安装依赖包"""
    try:
        import redis
        import requests
        from rich import console, progress, layout, panel
    except ImportError:
        console.print('[yellow]检测到缺少必要包！正在尝试安装！.....[/yellow]')
        import os
        os.system('pip install -r requirements.txt')
        
        # 重新导入以验证安装
        import redis
        import requests
        from rich import console, progress, layout, panel
        
        console.print('[green]依赖安装完成[/green]')

if __name__ == "__main__":
    try:
        check_dependencies()
        show_main_menu()
    except Exception as e:
        console.print(f"[red]程序启动失败：{str(e)}[/red]")
        sys.exit(1)
