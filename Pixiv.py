"""
P站小爬虫 爬每日排行榜
环境需求：Python3.6+ / Redis 
项目地址：https://github.com/nyaasuki/PixivSpider
支持 M1 芯片

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

    def __init__(self):
        self.ajax_url = 'https://www.pixiv.net/ajax/illust/{}/pages'  # id
        self.top_url = 'https://www.pixiv.net/ranking.php'
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    def get_list(self, pid):
        """
        :param pid: 插画ID
        """
        response = requests.get(self.ajax_url.format(pid), headers=self.headers, verify=False)
        json_data = response.json()
        list_temp = json_data['body']
        for l in list_temp:
            url_tamp = l['urls']['original']
            n = self.r.get(pid)
            if not n:
                why_not_do = self.get_img(url_tamp)
                # 判断是否返回异常 如果有异常则取消这个页面的爬取 等待下次
                if why_not_do == 1:
                    return pid
            else:
                print(f'插画ID:{pid}已存在！')
                break

            # with open('pixiv.json', 'a', encoding='utf-8') as f:
            #     f.write(url_tamp + '\n')
            # 导出

    def get_img(self, url):
        """

        :param url: 作品页URL
        :return:
        """
        if not os.path.isdir('./img'):
            os.makedirs('./img')
        file_name = re.findall('/\d+/\d+/\d+/\d+/\d+/\d+/(.*)', url)[0]
        if os.path.isfile(f'./img/{file_name}'):
            print(f'文件：{file_name}已存在，跳过')
            #  单个文件存在并不能判断是否爬取过
            return 0
        print(f'开始下载：{file_name}')
        t = 0
        while t < 3:
            try:
                img_temp = requests.get(url, headers=self.headers, timeout=15, verify=False)
                break
            except requests.exceptions.RequestException:
                print('连接异常！正在重试！')
                t += 1
        if t == 3:
            # 返回异常 取消此次爬取 等待下次
            return 1
        with open(f'./img/{file_name}', 'wb') as fp:
            fp.write(img_temp.content)

    def get_top_url(self, num):
        """

        :param num: 页码
        :return:
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
        for url in self.data:
            illust_id = url['illust_id']
            illust_user = url['user_id']
            yield illust_id  # 生成PID
            self.r.set(illust_id, illust_user)

    @classmethod
    def pixiv_spider_go(cls, data):
        cls.data = data

    @classmethod
    def pixiv_main(cls):
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
        print('开始抓取...')
        for i in range(1, 11, 1):  # p站每日排行榜最多为500个
            pixiv.get_top_url(i)
            for j in pixiv.get_top_pic():
                k = pixiv.get_list(j)  # 接口暂时不想写了 先这样凑合一下吧
                if k:
                    error_list.append(k)
        for k in error_list:
            pixiv.r.delete(k)


if __name__ == '__main__':
    pixiv = PixivSpider()
    pixiv.pixiv_main()
    # for id_url in pixiv.get_list():
    #     pixiv.get_img(id_url)
