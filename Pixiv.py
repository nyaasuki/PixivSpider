"""
P站小爬虫 爬每日排行榜
环境需求：Python3.6+ / Redis 
项目地址：https://github.com/nyaasuki/PixivSpider
支持 M1 芯片

"""

"""

                    载   入   区   域
--------------------------------------------------------------

"""

import os
import re
from cmd import Cmd

from lxml import html


try:

    import redis
    from requests_html import HTMLSession,requests
except:
    print('[System] 检测到缺少必要包！正在尝试安装！.....')
    os.system(r'pip install -r requirements.txt')
    import redis
    from requests_html import HTMLSession,requests

requests.packages.urllib3.disable_warnings()  # 解决报错
error_list = []

"""

           V   1   .   0   祖   传   代   码   区   域   
---------------------------------------------------------------------

"""


class PixivSpider(Cmd):
    prompt = 'Pixiv>'


    def __init__(self):
        super().__init__()
        self.ajax_url = 'https://www.pixiv.net/ajax/illust/{}/pages'  # id
        self.top_url = 'https://www.pixiv.net/ranking.php'
        self.home_url = 'https://www.pixiv.net/users/{}'
        self.stars_url = 'https://www.pixiv.net/users/{}/bookmarks/artworks'
        self.session = HTMLSession()
        self.r = redis.Redis(host='localhost', port=6379,decode_responses=True)

    def get_list(self, pid):
        """
        :param pid: 插画ID
        """
        response = self.session.get(self.ajax_url.format(pid), headers=temp_headers, verify=False)
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
                img_temp = self.session.get(
                    url, headers=self.headers, timeout=15, verify=False)
                break
            except self.session.exceptions.RequestException:
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
        response = self.session.get(self.top_url, params=params, headers=temp_headers, verify=False)
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
        print('开始抓取...')
        for i in range(1, 11, 1):  # p站每日排行榜最多为500个
            pixiv.get_top_url(i)
            for j in pixiv.get_top_pic():
                k = pixiv.get_list(j)  # 接口暂时不想写了 先这样凑合一下吧
                if k:
                    error_list.append(k)
        for k in error_list:
            pixiv.r.delete(k)
    
    def main(self):  # 全新的古老循环
        global uid , cookie ,temp_headers
        uid = pixiv.r.get('uid')
        cookie = pixiv.r.get('cookie')
        if not cookie:
            print('[Pixiv] 未检测到保存的cookie，此项可不输入，但是部分功能受限！')
            cookie = input('[Pixiv] 请输入一个cookie：')
            if not cookie:
                pixiv.cmdloop()
        if not uid:
             print('[Pixiv] 未检测到保存的UID，此UID必须配合Cookie使用，可以爬取某个用户的（包括不限于自己）收藏的插画！')
             uid = input('[Pixiv] 请输入一个uid：')
             pixiv.r.set('uid', uid)
        if not uid:
            print('[Redis] 未输入uid，部分功能受限')
        else:
            print(f'[Redis] 成功读取uid：{uid}')
            print('[Pixiv] 正在连接至Pixiv.....')
        temp_headers = {
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'dnt': '1',
            'cookie': f'{cookie}',
            'referer': 'https://www.pixiv.net/',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15'
            }

        try:
            response = self.session.get(self.home_url.format(uid), headers = temp_headers, verify=False)
            user_name = re.findall('og:title" content="(.*?)">', response.text)
            if not user_name:
                print('[Pixiv] 未查询到ID，请检查您的uid是否输入正确！')
                print('[Redis] 正在清除uid记录.....')
                self.r.delete('uid')
                self.main()
            print(f'[Pixiv] 欢迎～{user_name[0]}!')
            print('[System] 初始化中...第一次运行本程序时该过程需要一段时间...')
            # self.session.get('https://pixiv.net',headers = temp_headers, verify = False).html.render()
            print('[System] 初始化完成。')
            print('[Pixiv] 是不是觉得迷茫呢？请输入help来获取帮助吧！')
            print('[Pixiv] 我只能看得懂普通的小写字母哦！！！')
        except:
            print('[Pixiv] 未能连接到Pixiv服务器，请检查您的网络。')
            exit()
        
        self.do_stars(self)
        # self.cmdloop()

    def default(self, line):
        print('[Pixiv] 没有查询到该指令！')

    def do_help(self, arg):
        print('…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·')
        print('[Help] rank  - 爬取 Pixiv每日排行榜前500的插画')
        print('[Help] stars - 爬取 你已经添加❤的插画  *需要用户UID*')
        print('[Help] uid  - 更换已保存的uid')
        print('[Help] quit  - 退出程序')
        print('…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·…·')

    def do_quit(self, arg):
        exit()

    def emptyline(self):
        print ('请输入指令！输入help可查看帮助！')

    def do_rank(self, arg):
        self.pixiv_main()

    def do_stars(self, arg):
        if not uid:
            print('[Pixiv] 您未输入uid，无法使用本功能哦！')
            self.main()
        res = self.session.get(self.stars_url.format(uid), headers = temp_headers, verify=False)
        res.html.render()
        # css = res.html.find('#illust_id')
        # print(css)
        pass

    def do_like(self, arg):
        pass

    def do_uid(self, arg):
        pixiv.r.delete('uid')
        print('[Redis] uid清除完成了喵！')
        self.main()


"""

                     启   动   区   域
----------------------------------------------------------

"""

if __name__ == '__main__':
    pixiv = PixivSpider()
    pixiv.main()
    # for id_url in pixiv.get_list():
    #     pixiv.get_img(id_url)
