"""
Pixiv爬虫 - 每日排行榜下载
环境需求：Python3.8+ / Redis 
"""
from typing import Generator, List, Dict, Any
import requests
from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    TaskProgressColumn,
    TextColumn,
    SpinnerColumn
)
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Group

from config import PIXIV_CONFIG
from redis_client import RedisClient
from pixiv_download import PixivDownloader

requests.packages.urllib3.disable_warnings()

class PixivSpider:
    """Pixiv每日排行榜爬虫"""
    
    TOTAL_IMAGES = 500  # 每日排行榜总图片数
    
    def __init__(self, db: int = 0):
        """
        初始化爬虫
        
        参数:
            db: Redis数据库编号(0-5)
        """
        # 设置Redis
        self.redis = RedisClient()
        if not self.redis.select_db(db):
            raise ValueError(f"无效的Redis数据库编号: {db}")
            
        # 设置界面组件
        self.console = Console()
        self._setup_ui()
        
        # 初始化状态
        self.headers = None
        self.current_ranking_data = []
        self.failed_works = []
        
    def _setup_ui(self) -> None:
        """设置Rich界面组件"""
        # 创建布局
        self.layout = Layout()
        self.layout.split(
            Layout(name="PixivSpider", ratio=8),
            Layout(name="progress", ratio=2)
        )
        
        # 创建进度条
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TextColumn("{task.fields[speed]}"),
            console=Console(stderr=True),
            expand=True
        )
        
        # 设置日志面板
        self.log_messages = []
        self.main_task_id = self.progress.add_task(
            "[cyan]总体进度",
            total=self.TOTAL_IMAGES,
            speed=""
        )
        
    def _update_log(self, message: str) -> None:
        """更新日志显示"""
        self.log_messages.append(message)
        if len(self.log_messages) > 18:
            self.log_messages.pop(0)
        log_group = Group(*self.log_messages)
        self.layout["PixivSpider"].update(
            Panel(
                log_group,
                title="PixivSpider",
                title_align="left",
                border_style="cyan",
                padding=(0, 1)
            )
        )
        
    def _setup_session(self) -> None:
        """设置请求会话"""
        cookie = self.redis.get_cookie()
        if not cookie:
            cookie = input('请输入一个cookie：')
            self.redis.set_cookie(cookie)
            
        self.headers = PIXIV_CONFIG.headers.copy()
        self.headers['cookie'] = cookie
        
    def get_ranking_page(self, page: int) -> None:
        """
        获取排行榜单页数据
        
        参数:
            page: 页码(1-10)
        """
        params = {
            'mode': 'daily',
            'content': 'illust',
            'p': str(page),
            'format': 'json'
        }
        
        response = requests.get(
            PIXIV_CONFIG.top_url,
            params=params,
            headers=self.headers,
            verify=False
        )
        data = response.json()
        self.current_ranking_data = data['contents']
        
    def process_ranking_data(self) -> Generator[str, None, None]:
        """
        处理当前排行榜数据
        
        生成:
            str: 作品ID
        """
        for item in self.current_ranking_data:
            work_id = str(item['illust_id'])
            user_id = str(item['user_id'])
            self.redis.store_user_id(work_id, user_id)
            yield work_id
            
    def run(self) -> None:
        """运行爬虫"""
        self._setup_session()
        downloader = PixivDownloader(self.headers, self.progress)
        
        with Live(self.layout, self.console, refresh_per_second=10):
            self.layout["progress"].update(self.progress)
            self._update_log('[cyan]开始抓取...[/cyan]')
            
            # 处理排行榜页面
            for page in range(1, 11):
                try:
                    self.get_ranking_page(page)
                    for work_id in self.process_ranking_data():
                        if not downloader.download_work(work_id):
                            self.failed_works.append(work_id)
                        self.progress.update(self.main_task_id, advance=1)
                        
                except requests.RequestException as e:
                    self._update_log(f'[red]获取排行榜第{page}页时发生错误：{str(e)}[/red]')
                    continue
                    
            # 清理失败作品的记录
            for work_id in self.failed_works:
                self.redis.client.delete(work_id)
                
            self._update_log('[green]爬虫运行完成[/green]')
