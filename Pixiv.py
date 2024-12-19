"""
P站小爬虫 爬每日排行榜
环境需求：Python3.8+ / Redis 
项目地址：https://github.com/nyaasuki/PixivSpider

"""

import re
import os

try:
    import requests
    import redis

except:
    print('检测到缺少必要包！正在尝试安装！.....')
    os.system(r'pip install -r requirements.txt')
    import requests
    import redis

requests.packages.urllib3.disable_warnings()
error_list = []


class PixivSpider(object):

    def __init__(self, db=0):
        self.ajax_url = 'https://www.pixiv.net/ajax/illust/{}/pages'  # id
        self.top_url = 'https://www.pixiv.net/ranking.php'
        self.r = redis.Redis(host='localhost', port=6379, db=db, decode_responses=True)

    def get_list(self, pid):
        """
        获取作品所有页面的URL
        :param pid: 作品ID
        """
        try:
            # 检查Redis中是否已记录该作品已完全下载
            if self.r.get(f'downloaded:{pid}') == 'complete':
                print(f'作品ID:{pid}已在Redis中标记为完全下载，跳过')
                return None

            # 发送请求获取作品的所有图片信息
            response = requests.get(self.ajax_url.format(pid), headers=self.headers, verify=False)
            json_data = response.json()
            
            # 检查API返回是否有错误
            if json_data.get('error'):
                print(f'获取作品ID:{pid}失败：{json_data.get("message")}')
                return pid
                
            # 从返回数据中获取图片列表
            images = json_data.get('body', [])
            if not images:
                print(f'作品ID:{pid}没有图片')
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
                            print(f'发现本地文件并更新Redis记录：{f}')
            
            # 使用Redis记录作为唯一来源
            downloaded = downloaded_redis
            
            # 遍历所有图片进行下载
            for image in images:
                # 检查图片数据格式是否正确
                if 'urls' not in image or 'original' not in image['urls']:
                    print(f'作品ID:{pid}的图片数据格式错误')
                    continue
                    
                # 获取原图URL和页码信息
                original_url = image['urls']['original']
                page_num = int(re.search(r'_p(\d+)\.', original_url).group(1))
                
                # 检查是否已下载过该页面（优先使用Redis记录）
                if page_num in downloaded:
                    print(f'作品ID:{pid} 第{page_num}页在Redis中已标记为下载，跳过')
                    continue
                    
                # 下载图片，如果下载失败返回作品ID以便后续处理
                why_not_do = self.get_img(original_url)
                if why_not_do == 1:
                    return pid
                    
        except requests.exceptions.RequestException as e:
            print(f'获取作品ID:{pid}时发生网络错误：{str(e)}')
            return pid
        except Exception as e:
            print(f'处理作品ID:{pid}时发生错误：{str(e)}')
            return pid

    def get_img(self, url):
        """
        下载单个图片
        :param url: 原图URL，格式如：https://i.pximg.net/img-original/img/2024/12/14/20/00/36/125183562_p0.jpg
        :return: 0表示下载成功，1表示下载失败
        """
        # 确保下载目录存在
        if not os.path.isdir('./img'):
            os.makedirs('./img')
        
        # 从URL提取作品ID、页码和文件扩展名
        match = re.search(r'/(\d+)_p(\d+)\.([a-z]+)$', url)
        if not match:
            print(f'无效的URL格式: {url}')
            return 1
            
        # 解析URL信息并构建文件名
        illust_id, page_num, extension = match.groups()
        file_name = f"{illust_id}_p{page_num}.{extension}"
        
        # 检查Redis中是否已记录为下载
        if self.r.get(f'downloaded:{illust_id}_p{page_num}') == 'true':
            print(f'Redis记录：{file_name}已下载，跳过')
            return 0
            
        # 作为备份检查，验证文件是否存在
        if os.path.isfile(f'./img/{file_name}'):
            # 如果文件存在但Redis没有记录，更新Redis记录
            self.r.set(f'downloaded:{illust_id}_p{page_num}', 'true')
            print(f'文件已存在但Redis未记录，已更新Redis：{file_name}')
            return 0
            
        # 开始下载流程
        print(f'开始下载：{file_name} (第{int(page_num)+1}张)')
        t = 0  # 重试计数器
        # 最多重试3次
        while t < 3:
            try:
                # 下载图片，设置15秒超时
                img_temp = requests.get(url, headers=self.headers, timeout=15, verify=False)
                if img_temp.status_code == 200:
                    break
                print(f'下载失败，状态码：{img_temp.status_code}')
                t += 1
            except requests.exceptions.RequestException as e:
                print(f'连接异常：{str(e)}')
                t += 1
        
        # 如果重试3次都失败，放弃下载
        if t == 3:
            print(f'下载失败次数过多，跳过该图片')
            return 1
            
        # 将图片内容写入文件
        with open(f'./img/{file_name}', 'wb') as fp:
            fp.write(img_temp.content)
            
        # 下载成功后在Redis中记录
        self.r.set(f'downloaded:{illust_id}_p{page_num}', 'true')
        # 获取作品总页数并检查是否已下载所有页面
        page_count = self.r.get(f'total_pages:{illust_id}')
        if not page_count:
            # 当前页号+1可能是总页数（保守估计）
            self.r.set(f'total_pages:{illust_id}', str(int(page_num) + 1))
        elif int(page_num) + 1 == int(page_count):
            # 如果当前是最后一页，检查是否所有页面都已下载
            all_downloaded = all(
                self.r.get(f'downloaded:{illust_id}_p{i}') == 'true'
                for i in range(int(page_count))
            )
            if all_downloaded:
                self.r.set(f'downloaded:{illust_id}', 'complete')
                print(f'作品ID:{illust_id}已完全下载')
            
        print(f'下载完成并已记录到Redis：{file_name}')
        return 0

    def get_top_url(self, num):
        """
        获取每日排行榜的特定页码数据
        :param num: 页码数（1-10）
        :return: None
        """
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
        """
        从排行榜数据中提取作品ID和用户ID
        并将用户ID存入Redis数据库中
        :return: 生成器，返回作品ID
        """
        for url in self.data:
            illust_id = url['illust_id']  # 获取作品ID
            illust_user = url['user_id']  # 获取用户ID
            yield illust_id  # 生成作品ID
            self.r.set(illust_id, illust_user)  # 将PID保存到Redis中

    @classmethod
    def pixiv_spider_go(cls, data):
        """
        存储排行榜数据供后续处理
        :param data: 排行榜JSON数据中的contents部分
        """
        cls.data = data

    @classmethod
    def pixiv_main(cls):
        """
        爬虫主函数
        1. 选择Redis数据库
        2. 获取或设置Cookie
        3. 配置请求头
        4. 遍历排行榜页面（1-10页）
        5. 下载每个作品的所有图片
        6. 处理下载失败的作品
        """
        # 选择Redis数据库
        while True:
            try:
                print("\n可用的Redis数据库:")
                for i in range(6):
                    print(f"{i}.DB{i}")
                db_choice = input("\n请选择Redis数据库 (0-5): ")
                db_num = int(db_choice)
                if 0 <= db_num <= 5:
                    break
                print("错误：请输入0到5之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")
        
        global pixiv
        pixiv = PixivSpider(db_num)
        print(f"\n已选择 DB{db_num}")
        
        # 从Redis获取Cookie，如果没有则要求用户输入
        cookie = pixiv.r.get('cookie')
        if not cookie:
            cookie = input('请输入一个cookie：')
            pixiv.r.set('cookie', cookie)
            
        # 配置请求头，包含必要的HTTP头部信息
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
        
        print('开始抓取...')
        # 遍历排行榜前10页
        for i in range(1, 11, 1):  # p站每日排行榜最多为500个（50个/页 x 10页）
            pixiv.get_top_url(i)  # 获取当前页的排行榜数据
            for j in pixiv.get_top_pic():  # 遍历当前页的所有作品
                k = pixiv.get_list(j)  # 下载作品的所有图片
                if k:  # 如果下载失败，将作品ID添加到错误列表
                    error_list.append(k)
                    
        # 清理下载失败的作品记录
        for k in error_list:
            pixiv.r.delete(k)


if __name__ == '__main__':
    try:
        print('正在启动Pixiv爬虫...')
        print('确保已安装并启动Redis服务')
        print('确保已准备好有效的Pixiv Cookie')
        
        # 运行主程序
        PixivSpider.pixiv_main()
        
        print('爬虫运行完成')
    except redis.exceptions.ConnectionError:
        print('错误：无法连接到Redis服务，请确保Redis服务正在运行')
    except KeyboardInterrupt:
        print('\n用户中断运行')
    except Exception as e:
        print(f'发生错误：{str(e)}')
