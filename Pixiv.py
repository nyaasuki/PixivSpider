"""
P站小爬虫 爬每日排行榜
环境需求：Python3.8+ / Redis 
项目地址：https://github.com/nyaasuki/PixivSpider
"""

import re
import os
import sys
import time

try:
    import requests
    import redis
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TextColumn, SpinnerColumn
    from rich.live import Live
    from rich.layout import Layout

except:
    print('检测到缺少必要包！正在尝试安装！.....')
    os.system(r'pip install -r requirements.txt')
    import requests
    import redis
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TextColumn, SpinnerColumn
    from rich.live import Live
    from rich.layout import Layout

requests.packages.urllib3.disable_warnings()
error_list = []

# 创建Console对象用于日志输出
console = Console()

# 创建Layout布局
layout = Layout()
layout.split(
    Layout(name="PixivSpider", ratio=8),
    Layout(name="progress", ratio=2)
)

# 创建日志面板并设置样式
from rich.panel import Panel
from rich.live import Live
from rich.console import Group

# 创建日志存储列表
log_messages = []

def update_log(message):
    """更新日志显示"""
    log_messages.append(message)
    if len(log_messages) > 18:  # 保持最近的18条日志
        log_messages.pop(0)
    log_group = Group(*log_messages)
    layout["PixivSpider"].update(
        Panel(
            log_group,
            title="PixivSpider",
            title_align="left",
            border_style="cyan",
            padding=(0, 1)
        )
    )

# 创建Console对象用于日志输出
console = Console()

def format_speed(speed):
    """格式化速度显示，保留两位小数并添加单位"""
    return f"{speed:.2f}t/秒" if speed is not None else ""

# 创建进度条
progress = Progress(
    TextColumn("[bold blue]{task.description}"),
    BarColumn(bar_width=40),
    TaskProgressColumn(),
    TextColumn("{task.fields[speed]}"),
    console=Console(stderr=True),  # 使用stderr以避免与日志混合
    expand=True,
)

class PixivSpider(object):
    # 类变量用于跟踪总体进度
    total_images = 500  # 每日排行榜总图片数
    main_task_id = None  # 主任务ID
    current_subtask_id = None  # 当前子任务ID

    def __init__(self, db=0):
        self.ajax_url = 'https://www.pixiv.net/ajax/illust/{}/pages'  # id
        self.top_url = 'https://www.pixiv.net/ranking.php'
        self.r = redis.Redis(host='localhost', port=6379, db=db, decode_responses=True)
        # 创建进度显示所需的任务
        with Live(layout, console=console, refresh_per_second=10):
            cls = self.__class__
            if not cls.main_task_id:
                layout["progress"].update(progress)
                cls.main_task_id = progress.add_task("[cyan]总体进度", total=cls.total_images, speed="")

    def get_list(self, pid):
        """获取作品所有页面的URL"""
        try:
            # 检查Redis中是否已记录该作品已完全下载
            if self.r.get(f'downloaded:{pid}') == 'complete':
                update_log(f'[yellow]作品ID:{pid}已在Redis中标记为完全下载，跳过[/yellow]')
                progress.update(self.__class__.main_task_id, advance=1)
                return None

            # 发送请求获取作品的所有图片信息
            response = requests.get(self.ajax_url.format(pid), headers=self.headers, verify=False)
            json_data = response.json()
            
            # 检查API返回是否有错误
            if json_data.get('error'):
                update_log(f'[red]获取作品ID:{pid}失败：{json_data.get("message")}[/red]')
                return pid
                
            # 从返回数据中获取图片列表
            images = json_data.get('body', [])
            if not images:
                update_log(f'[red]作品ID:{pid}没有图片[/red]')
                return pid
                
            # 获取Redis中已下载的页面记录
            downloaded_redis = set()
            for i in range(len(images)):
                if self.r.get(f'downloaded:{pid}_p{i}') == 'true':
                    downloaded_redis.add(i)

            # 检查本地已下载的文件并更新Redis记录
            if os.path.exists('./img'):
                for f in os.listdir('./img'):
                    if f.startswith(f'{pid}_p'):
                        page = int(re.search(r'_p(\d+)\.', f).group(1))
                        if self.r.get(f'downloaded:{pid}_p{page}') != 'true':
                            self.r.set(f'downloaded:{pid}_p{page}', 'true')
                            update_log(f'[green]发现本地文件并更新Redis记录：{f}[/green]')
            
            # 使用Redis记录作为唯一来源
            downloaded = downloaded_redis
            
            # 遍历所有图片进行下载
            if len(images) > 1:
                # 对于多图片组，创建子进度条
                with progress:
                    subtask_id = progress.add_task(
                        f"[yellow]PID:{pid}",
                        total=len(images),
                        visible=True,
                        speed=""
                    )
                    for image in images:
                        if 'urls' not in image or 'original' not in image['urls']:
                            update_log(f'[red]作品ID:{pid}的图片数据格式错误[/red]')
                            progress.update(subtask_id, advance=1)
                            continue
                            
                        original_url = image['urls']['original']
                        page_num = int(re.search(r'_p(\d+)\.', original_url).group(1))
                        
                        if page_num in downloaded:
                            update_log(f'[yellow]作品ID:{pid} 第{page_num}页在Redis中已标记为下载，跳过[/yellow]')
                            progress.update(subtask_id, advance=1)
                            continue
                            
                        why_not_do = self.get_img(original_url)
                        progress.update(subtask_id, advance=1)
                        if why_not_do == 1:
                            return pid
                    progress.remove_task(subtask_id)
            else:
                # 单图片直接处理
                for image in images:
                    if 'urls' not in image or 'original' not in image['urls']:
                        update_log(f'[red]作品ID:{pid}的图片数据格式错误[/red]')
                        continue
                        
                    original_url = image['urls']['original']
                    page_num = int(re.search(r'_p(\d+)\.', original_url).group(1))
                    
                    if page_num in downloaded:
                        update_log(f'[yellow]作品ID:{pid} 第{page_num}页在Redis中已标记为下载，跳过[/yellow]')
                        continue
                        
                    why_not_do = self.get_img(original_url)
                    if why_not_do == 1:
                        return pid
            
            # 更新总进度
            progress.update(self.__class__.main_task_id, advance=1)
                    
        except requests.exceptions.RequestException as e:
            update_log(f'[red]获取作品ID:{pid}时发生网络错误：{str(e)}[/red]')
            return pid
        except Exception as e:
            update_log(f'[red]处理作品ID:{pid}时发生错误：{str(e)}[/red]')
            return pid

    def get_img(self, url):
        """下载单个图片"""
        # 确保下载目录存在
        if not os.path.isdir('./img'):
            os.makedirs('./img')
        
        # 从URL提取作品ID、页码和文件扩展名
        match = re.search(r'/(\d+)_p(\d+)\.([a-z]+)$', url)
        if not match:
            update_log(f'[red]无效的URL格式: {url}[/red]')
            return 1
            
        # 解析URL信息并构建文件名
        illust_id, page_num, extension = match.groups()
        file_name = f"{illust_id}_p{page_num}.{extension}"
        
        # 检查Redis中是否已记录为下载
        if self.r.get(f'downloaded:{illust_id}_p{page_num}') == 'true':
            update_log(f'[yellow]Redis记录：{file_name}已下载，跳过[/yellow]')
            return 0
            
        # 作为备份检查，验证文件是否存在
        if os.path.isfile(f'./img/{file_name}'):
            self.r.set(f'downloaded:{illust_id}_p{page_num}', 'true')
            update_log(f'[green]文件已存在但Redis未记录，已更新Redis：{file_name}[/green]')
            return 0
            
        # 开始下载流程
        update_log(f'[cyan]开始下载：{file_name} (第{int(page_num)+1}张)[/cyan]')
        t = 0  # 重试计数器
        while t < 3:
            try:
                img_temp = requests.get(url, headers=self.headers, timeout=15, verify=False)
                if img_temp.status_code == 200:
                    break
                update_log(f'[red]下载失败，状态码：{img_temp.status_code}[/red]')
                t += 1
            except requests.exceptions.RequestException as e:
                update_log(f'[red]连接异常：{str(e)}[/red]')
                t += 1
        
        if t == 3:
            update_log(f'[red]下载失败次数过多，跳过该图片[/red]')
            return 1
            
        # 将图片内容写入文件
        with open(f'./img/{file_name}', 'wb') as fp:
            fp.write(img_temp.content)
            
        # 下载成功后在Redis中记录
        self.r.set(f'downloaded:{illust_id}_p{page_num}', 'true')
        page_count = self.r.get(f'total_pages:{illust_id}')
        if not page_count:
            self.r.set(f'total_pages:{illust_id}', str(int(page_num) + 1))
        elif int(page_num) + 1 == int(page_count):
            all_downloaded = all(
                self.r.get(f'downloaded:{illust_id}_p{i}') == 'true'
                for i in range(int(page_count))
            )
            if all_downloaded:
                self.r.set(f'downloaded:{illust_id}', 'complete')
                update_log(f'[green]作品ID:{illust_id}已完全下载[/green]')
            
        if not self.r.exists(f'total_pages:{illust_id}') or int(page_num) == 0:
            # 单图片直接显示下载完成信息
            update_log(f'[green]{file_name} 已下载![/green]')
        else:
            # 多图片组显示详细信息
            update_log(f'[green]下载完成并已记录到Redis：{file_name}[/green]')
        return 0

    def get_top_url(self, num):
        """获取每日排行榜的特定页码数据"""
        params = {
            'mode': 'daily',
            'content': 'illust',
            'p': f'{num}',
            'format': 'json'
        }
        response = requests.get(self.top_url, params=params, headers=self.headers, verify=False)
        json_data = response.json()
        self.pixiv_spider_go(json_data['contents'])

    def get_top_pic(self):
        """从排行榜数据中提取作品ID和用户ID"""
        for url in self.data:
            illust_id = url['illust_id']
            illust_user = url['user_id']
            yield illust_id
            self.r.set(illust_id, illust_user)

    @classmethod
    def pixiv_spider_go(cls, data):
        """存储排行榜数据供后续处理"""
        cls.data = data

    @classmethod
    def pixiv_main(cls):
        """爬虫主函数"""
        while True:
            try:
                console.print("\n[cyan]可用的Redis数据库:[/cyan]")
                for i in range(6):
                    console.print(f"{i}.DB{i}")
                db_choice = input("\n请选择Redis数据库 (0-5): ")
                db_num = int(db_choice)
                if 0 <= db_num <= 5:
                    break
                console.print("[red]错误：请输入0到5之间的数字[/red]")
            except ValueError:
                console.print("[red]错误：请输入有效的数字[/red]")
        
        global pixiv
        pixiv = PixivSpider(db_num)
        console.print(f"\n[green]已选择 DB{db_num}[/green]")
        
        cookie = pixiv.r.get('cookie')
        if not cookie:
            cookie = input('请输入一个cookie：')
            pixiv.r.set('cookie', cookie)
            
        cls.headers = {
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'dnt': '1',
            'cookie': f'{cookie}',
            'referer': 'https://www.pixiv.net/',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
        }
        
        console.print('[cyan]开始抓取...[/cyan]')
        
        start_time = time.time()  # 添加计时器用于计算速度
        processed_count = 0  # 记录已处理的图片数量
        
        with Live(layout, console=console, refresh_per_second=10):
            layout["progress"].update(progress)
            # 遍历排行榜前10页
            for i in range(1, 11, 1):
                pixiv.get_top_url(i)
                for j in pixiv.get_top_pic():
                    k = pixiv.get_list(j)
                    if k:
                        error_list.append(k)
                    
                    # 更新处理计数和速度
                    processed_count += 1
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        speed = processed_count / elapsed
                        progress.update(pixiv.__class__.main_task_id, speed=format_speed(speed))
            
            # 清理下载失败的作品记录
            for k in error_list:
                pixiv.r.delete(k)

if __name__ == '__main__':
    try:
        console.print('[cyan]正在启动Pixiv爬虫...[/cyan]')
        console.print('[yellow]确保已安装并启动Redis服务[/yellow]')
        console.print('[yellow]确保已准备好有效的Pixiv Cookie[/yellow]')
        
        PixivSpider.pixiv_main()
        
        console.print('[green]爬虫运行完成[/green]')
    except redis.exceptions.ConnectionError:
        console.print('[red]错误：无法连接到Redis服务，请确保Redis服务正在运行[/red]')
    except KeyboardInterrupt:
        console.print('\n[yellow]用户中断运行[/yellow]')
    except Exception as e:
        console.print(f'[red]发生错误：{str(e)}[/red]')
