"""Redis客户端管理"""
from typing import Optional
import redis
from redis.connection import ConnectionPool
from config import REDIS_CONFIG, RedisKeys

class RedisClient:
    """Redis客户端管理器，使用连接池"""
    _pools: dict[int, ConnectionPool] = {}
    _instance: Optional['RedisClient'] = None

    def __new__(cls) -> 'RedisClient':
        """确保单例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化客户端管理器"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._current_db = 0
            self._redis: Optional[redis.Redis] = None
            self._init_connection()

    def _get_pool(self, db: int) -> ConnectionPool:
        """获取指定数据库的连接池"""
        if db not in self._pools:
            self._pools[db] = redis.ConnectionPool(
                host=REDIS_CONFIG.host,
                port=REDIS_CONFIG.port,
                db=db,
                max_connections=REDIS_CONFIG.max_connections,
                decode_responses=True
            )
        return self._pools[db]

    def _init_connection(self) -> None:
        """初始化当前数据库的连接"""
        self._redis = redis.Redis(
            connection_pool=self._get_pool(self._current_db)
        )

    def select_db(self, db: int) -> bool:
        """
        切换到指定数据库
        
        参数:
            db: 数据库编号
            
        返回:
            bool: 成功返回True，失败返回False
        """
        min_db, max_db = REDIS_CONFIG.db_range
        if not min_db <= db <= max_db:
            return False
            
        if db != self._current_db:
            self._current_db = db
            self._init_connection()
        return True

    @property
    def client(self) -> redis.Redis:
        """获取当前Redis客户端"""
        return self._redis

    def get_cookie(self) -> Optional[str]:
        """获取存储的Pixiv cookie"""
        return self._redis.get(RedisKeys.COOKIE)

    def set_cookie(self, cookie: str) -> None:
        """存储Pixiv cookie"""
        self._redis.set(RedisKeys.COOKIE, cookie)

    def is_image_downloaded(self, pid: str, page: int) -> bool:
        """检查特定图片页是否已下载"""
        key = RedisKeys.DOWNLOADED_IMAGE.format(pid=pid, page=page)
        return self._redis.get(key) == 'true'

    def mark_image_downloaded(self, pid: str, page: int) -> None:
        """标记特定图片页为已下载"""
        key = RedisKeys.DOWNLOADED_IMAGE.format(pid=pid, page=page)
        self._redis.set(key, 'true')

    def is_work_complete(self, pid: str) -> bool:
        """检查作品是否已完全下载"""
        key = RedisKeys.DOWNLOADED_WORK.format(pid=pid)
        return self._redis.get(key) == 'complete'

    def mark_work_complete(self, pid: str) -> None:
        """标记作品为已完全下载"""
        key = RedisKeys.DOWNLOADED_WORK.format(pid=pid)
        self._redis.set(key, 'complete')

    def get_total_pages(self, pid: str) -> Optional[int]:
        """获取作品总页数"""
        key = RedisKeys.TOTAL_PAGES.format(pid=pid)
        value = self._redis.get(key)
        return int(value) if value else None

    def set_total_pages(self, pid: str, total: int) -> None:
        """设置作品总页数"""
        key = RedisKeys.TOTAL_PAGES.format(pid=pid)
        self._redis.set(key, str(total))

    def store_user_id(self, illust_id: str, user_id: str) -> None:
        """存储作品作者ID"""
        key = RedisKeys.USER_ID.format(illust_id=illust_id)
        self._redis.set(key, user_id)

    def get_db_stats(self) -> tuple[int, list[str]]:
        """
        获取当前数据库统计信息
        
        返回:
            tuple: (作品数量, 作品ID列表)
        """
        pattern = RedisKeys.DOWNLOADED_IMAGE.format(pid='*', page='0')
        work_keys = self._redis.keys(pattern)
        work_ids = [key.split(':')[1].split('_')[0] for key in work_keys]
        return len(work_ids), work_ids

    def clear_db(self) -> None:
        """清空当前数据库"""
        self._redis.flushdb()

    def close(self) -> None:
        """关闭所有连接池"""
        for pool in self._pools.values():
            pool.disconnect()
        self._pools.clear()
