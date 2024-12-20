"""Pixiv下载组件"""
import os
import re
from typing import Optional, Union
import requests
from rich.progress import Progress

from config import PIXIV_CONFIG
from redis_client import RedisClient

class PixivDownloader:
    """处理Pixiv图片下载"""
    
    def __init__(self, headers: dict, progress: Progress):
        """
        初始化下载器
        
        参数:
            headers: 带cookie的请求头
            progress: Rich进度条实例
        """
        self.headers = headers
        self.progress = progress
        self.redis = RedisClient()

    def download_image(self, url: str) -> bool:
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
        
        # 检查是否已下载
        if self.redis.is_image_downloaded(illust_id, page_num):
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
                    
                    # 更新Redis记录
                    self.redis.mark_image_downloaded(illust_id, page_num)
                    
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
                    
            except requests.RequestException:
                if attempt == 2:  # 最后一次尝试失败
                    return False
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
                
            # 下载每张图片
            if len(images) > 1:
                # 多图作品
                subtask_id = self.progress.add_task(
                    f"[yellow]PID:{work_id}",
                    total=len(images)
                )
                
                success = True
                for image in images:
                    if 'urls' not in image or 'original' not in image['urls']:
                        success = False
                        continue
                        
                    if not self.download_image(image['urls']['original']):
                        success = False
                        
                    self.progress.update(subtask_id, advance=1)
                    
                self.progress.remove_task(subtask_id)
                return success
                
            else:
                # 单图作品
                if 'urls' not in images[0] or 'original' not in images[0]['urls']:
                    return False
                return self.download_image(images[0]['urls']['original'])
                
        except (requests.RequestException, KeyError, ValueError):
            return False
