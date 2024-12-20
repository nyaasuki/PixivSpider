"""Redis监控和管理工具"""
from typing import Optional, Dict
import sys
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from redis_client import RedisClient
from config import REDIS_CONFIG

console = Console()

class RedisMonitor:
    """Redis监控和管理界面"""
    
    def __init__(self):
        """初始化监控器"""
        self.redis = RedisClient()
        
    def _show_db_info(self, db_index: int) -> None:
        """
        显示数据库详细信息
        
        参数:
            db_index: 数据库编号
        """
        try:
            self.redis.select_db(db_index)
            
            table = Table(title=f"数据库 db{db_index} 信息")
            table.add_column("项目", style="cyan")
            table.add_column("值", style="green")
            
            # Cookie状态
            cookie = self.redis.get_cookie()
            table.add_row(
                "Cookie状态",
                cookie[:30] + "..." if cookie else "未设置"
            )
            
            # 作品统计
            work_count, work_ids = self.redis.get_db_stats()
            table.add_row("已下载作品数", str(work_count))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]获取数据库信息时出错：{str(e)}[/red]")
            
    def show_status(self) -> None:
        """显示Redis状态和数据库信息"""
        try:
            # 获取活跃数据库
            active_dbs = []
            min_db, max_db = REDIS_CONFIG.db_range
            for db in range(min_db, max_db + 1):
                if self.redis.select_db(db):
                    work_count, _ = self.redis.get_db_stats()
                    if work_count > 0:
                        active_dbs.append(db)
                        
            if not active_dbs:
                console.print("\n[yellow]当前没有活跃的数据库[/yellow]")
                return
                
            # 显示数据库列表
            db_list = ", ".join(f"db{db}" for db in active_dbs)
            console.print(f"\n[cyan]活跃的数据库: {db_list}[/cyan]")
            
            # 显示详细信息
            if len(active_dbs) == 1:
                self._show_db_info(active_dbs[0])
            else:
                while True:
                    db = Prompt.ask(
                        "请选择要查看的数据库编号",
                        choices=[str(db) for db in active_dbs]
                    )
                    self._show_db_info(int(db))
                    break
                    
        except Exception as e:
            console.print(f"[red]获取Redis状态时出错：{str(e)}[/red]")
            
    def clear_database(self) -> None:
        """清空Redis数据库"""
        try:
            # 获取活跃数据库
            active_dbs = []
            min_db, max_db = REDIS_CONFIG.db_range
            for db in range(min_db, max_db + 1):
                if self.redis.select_db(db):
                    work_count, _ = self.redis.get_db_stats()
                    if work_count > 0:
                        active_dbs.append(db)
                        
            if not active_dbs:
                console.print("\n[yellow]当前没有活跃的数据库[/yellow]")
                return
                
            # 显示数据库列表
            db_list = ", ".join(f"db{db}" for db in active_dbs)
            console.print(f"\n[cyan]活跃的数据库: {db_list}[/cyan]")
            
            # 显示选项
            console.print("\n清空选项:")
            console.print("1. 清空指定数据库")
            console.print("2. 清空所有数据库")
            console.print("3. 取消操作")
            
            choice = Prompt.ask("请选择操作", choices=["1", "2", "3"])
            
            if choice == "1":
                if len(active_dbs) == 1:
                    db = active_dbs[0]
                    if Confirm.ask(f"确定要清空数据库 db{db} 吗?"):
                        self.redis.select_db(db)
                        self.redis.clear_db()
                        console.print(f"[green]数据库 db{db} 已清空[/green]")
                else:
                    db = int(Prompt.ask(
                        "请选择要清空的数据库编号",
                        choices=[str(db) for db in active_dbs]
                    ))
                    if Confirm.ask(f"确定要清空数据库 db{db} 吗?"):
                        self.redis.select_db(db)
                        self.redis.clear_db()
                        console.print(f"[green]数据库 db{db} 已清空[/green]")
                        
            elif choice == "2":
                if Confirm.ask("确定要清空所有数据库吗?"):
                    for db in range(min_db, max_db + 1):
                        self.redis.select_db(db)
                        self.redis.clear_db()
                    console.print("[green]所有数据库已清空[/green]")
                    
        except Exception as e:
            console.print(f"[red]清空数据库时出错：{str(e)}[/red]")
            
    def run(self) -> None:
        """运行监控界面"""
        while True:
            console.print("\n=== Redis管理工具 ===")
            console.print("1. 显示状态")
            console.print("2. 清空数据库")
            console.print("3. 退出")
            
            try:
                choice = Prompt.ask("请选择操作", choices=["1", "2", "3"])
                
                if choice == "1":
                    self.show_status()
                elif choice == "2":
                    self.clear_database()
                else:
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]用户中断操作[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]发生错误：{str(e)}[/red]")
                
def show_menu() -> None:
    """Redis监控入口"""
    try:
        monitor = RedisMonitor()
        monitor.run()
    except Exception as e:
        console.print(f"[red]启动Redis管理工具时出错：{str(e)}[/red]")
        
if __name__ == '__main__':
    show_menu()
