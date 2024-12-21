"""Pixiv下载组件"""
import os
import re
from typing import Optional, Union
import requests
from rich.progress import Progress
from rich.console import Console

from config import PIXIV_CONFIG
from redis_client import RedisClient

class PixivDownloader:
    """处理Pixiv图片下载"""
    
    def __init__(self, spider, headers: dict, progress: Progress):
        """
        初始化下载器
        
        参数:
            spider: PixivSpider实例，用于日志更新
            headers: 带cookie的请求头
            progress: Rich进度条实例
        """
        self.spider = spider
        self.headers = headers
        self.progress = progress
        self.redis = RedisClient()
        # 用于追踪下载状态
        self.work_status = {}  # 记录每个作品的下载状态

    def download_image(self, url: str, work_id: str = None) -> bool:
        """
        下载单张图片
        
        参数:
            url: 图片URL
            
        返回:
            bool: 成功返回True，失败返回False
        """
        # 从URL提取图片信息
        match = re.search(r'/(\d+)_p(\d+)\.([a-z]+)$', url)
        if not match:
            return False
            
        illust_id, page_num, extension = match.groups()
        file_name = f"{illust_id}_p{page_num}.{extension}"
        
        # 检查文件是否已存在
        file_path = f'./img/{file_name}'
        if os.path.exists(file_path):
            self.spider._update_log(f"[green]{file_name} 已存在！[/green]")
            # 确保Redis状态同步
            if not self.redis.is_image_downloaded(illust_id, page_num):
                self.redis.mark_image_downloaded(illust_id, page_num)
            return True
            
        # 确保下载目录存在
        if not os.path.isdir('./img'):
            os.makedirs('./img')
            
        # 下载重试机制
        for attempt in range(3):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=15,
                    verify=False
                )
                if response.status_code == 200:
                    # 保存图片
                    with open(f'./img/{file_name}', 'wb') as fp:
                        fp.write(response.content)
                    
                    # 更新Redis记录并显示下载成功信息
                    self.redis.mark_image_downloaded(illust_id, page_num)
                    self.spider._update_log(f"[bold white]{file_name} 已下载！[/bold white]")
                    
                    # 更新总页数
                    total_pages = self.redis.get_total_pages(illust_id)
                    if not total_pages:
                        self.redis.set_total_pages(illust_id, int(page_num) + 1)
                    elif int(page_num) + 1 == total_pages:
                        # 检查作品是否完成
                        all_downloaded = all(
                            self.redis.is_image_downloaded(illust_id, i)
                            for i in range(total_pages)
                        )
                        if all_downloaded:
                            self.redis.mark_work_complete(illust_id)
                    
                    return True
                    
            except requests.RequestException as e:
                if attempt == 2:  # 最后一次尝试失败
                    error_msg = f"[red]下载失败(PID:{work_id}): {str(e)}[/red]"
                    self.spider._update_log(error_msg)
                    return False
                self.spider._update_log(f"[yellow]重试下载(PID:{work_id}): 第{attempt + 1}次[/yellow]")
                continue
                
        return False

    def download_work(self, work_id: str) -> bool:
        """
        下载作品的所有图片
        
        参数:
            work_id: Pixiv作品ID
            
        返回:
            bool: 全部成功返回True，否则False
        """
        # 跳过已完成的作品
        if self.redis.is_work_complete(work_id):
            if work_id not in self.work_status:
                self.spider._update_log(f"[green]作品(PID:{work_id})已完成下载[/green]")
                self.work_status[work_id] = "complete"
            return True
            
        try:
            # 获取图片URL列表
            response = requests.get(
                PIXIV_CONFIG.ajax_url.format(work_id),
                headers=self.headers,
                verify=False
            )
            data = response.json()
            
            if data.get('error'):
                return False
                
            images = data.get('body', [])
            if not images:
                return False
                
            try:
                # 下载每张图片
                if len(images) > 1:
                    # 多图作品
                    subtask_id = self.progress.add_task(
                        f"[yellow]PID:{work_id}",
                        total=len(images)
                    )
                    
                    success = True
                    for idx, image in enumerate(images):
                        if 'urls' not in image or 'original' not in image['urls']:
                            self.spider._update_log(f"[red]图片{idx + 1}URL获取失败(PID:{work_id})[/red]")
                            success = False
                            continue
                            
                        if not self.download_image(image['urls']['original'], work_id):
                            self.spider._update_log(f"[red]图片{idx + 1}下载失败(PID:{work_id})[/red]")
                            success = False
                        else:
                            self.spider._update_log(f"[green]图片{idx + 1}/{len(images)}下载完成(PID:{work_id})[/green]")
                            
                        self.progress.update(subtask_id, advance=1)
                        
                    self.progress.remove_task(subtask_id)
                    return success
                    
                else:
                    # 单图作品
                    if 'urls' not in images[0] or 'original' not in images[0]['urls']:
                        self.spider._update_log(f"[red]URL获取失败(PID:{work_id})[/red]")
                        return False
                    return self.download_image(images[0]['urls']['original'], work_id)
                    
            except Exception as e:
                self.spider._update_log(f"[red]作品处理出错(PID:{work_id}): {str(e)}[/red]")
                return False
                
        except (requests.RequestException, KeyError, ValueError) as e:
            self.spider._update_log(f"[red]作品信息获取失败(PID:{work_id}): {str(e)}[/red]")
            return False
