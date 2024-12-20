"""配置管理"""
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = 'localhost'
    port: int = 6379
    max_connections: int = 10
    db_range: tuple = (0, 5)  # 支持的数据库范围(包含)

@dataclass
class PixivConfig:
    """Pixiv API配置"""
    ajax_url: str = 'https://www.pixiv.net/ajax/illust/{}/pages'
    top_url: str = 'https://www.pixiv.net/ranking.php'
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
    headers: Dict[str, str] = None

    def __post_init__(self):
        """初始化默认请求头"""
        self.headers = {
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'dnt': '1',
            'referer': 'https://www.pixiv.net/',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': self.user_agent
        }

# 全局配置实例
REDIS_CONFIG = RedisConfig()
PIXIV_CONFIG = PixivConfig()

# Redis键模式
class RedisKeys:
    """Redis键定义"""
    COOKIE = 'cookie'
    DOWNLOADED_IMAGE = 'downloaded:{pid}_p{page}'  # 已下载的图片页
    DOWNLOADED_WORK = 'downloaded:{pid}'           # 已完成的作品
    TOTAL_PAGES = 'total_pages:{pid}'             # 作品总页数
    USER_ID = '{illust_id}'                       # 作品作者ID
