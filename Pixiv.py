import requests
import re
import os


class PixivSpider(object):
    def __init__(self):
        self.ajax_url = 'https://www.pixiv.net/ajax/illust/{}/pages'  # id
        self.headers = {
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'cookie': 'first_visit_datetime_pc=2019-09-08+17%3A21%3A54; p_ab_id=5; p_ab_id_2=0; p_ab_d_id=599112061; yuid_b=FDhIdJY; __utmc=235335808; privacy_policy_agreement=1; p_b_type=2; login_bc=1; _ga=GA1.2.947189649.1567930916; _gid=GA1.2.793259115.1568555659; PHPSESSID=17740269_d0a201fcc367f9a0e8510b1de840a8b3; device_token=d4fafe3d31fa7063581ea3b80e0d8cf6; c_type=23; a_type=0; b_type=1; d_type=1; module_orders_mypage=%5B%7B%22name%22%3A%22sketch_live%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22tag_follow%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22recommended_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22everyone_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22following_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22mypixiv_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22spotlight%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22fanbox%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22featured_tags%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22contests%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22user_events%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22sensei_courses%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22booth_follow_items%22%2C%22visible%22%3Atrue%7D%5D; is_sensei_service_user=1; login_ever=yes; __utmv=235335808.|2=login%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=17740269=1^9=p_ab_id=5=1^10=p_ab_id_2=0=1^11=lang=zh=1; __utma=235335808.947189649.1567930916.1568554491.1568560389.4; __utmz=235335808.1568560389.4.3.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/login; ki_t=1568561812088%3B1568561812088%3B1568562206475%3B1%3B5; tag_view_ranking=RTJMXD26Ak~Lt-oEicbBr~jH0uD88V6F~BU9SQkS-zU~jfnUZgnpFl~y8GNntYHsi~_pwIgrV8TB~CrFcrMFJzz~osjGBvsNDJ~1F9SMtTyiX~iFcW6hPGPU~EGefOqA6KB~BtXd1-LPRH~bo5e_8AN4e~B9WjdeT8q-~SQZaakhtVv~NBK37t_oSE~Hjx7wJwsUT~KvAGITxIxH~kxSeeOQL7R~OvYjFzHBbv~azESOjmQSV~doKLu5a3ct~qtVr8SCFs5~q303ip6Ui5~zIv0cf5VVk~ZlTwwXUT-f~di4yx918GB~ppw5N8XksW~metPG27dgT~BCV_kQ_qR_~75zhzbk0bS~l5WYRzHH5-~CvNLjkK_C2~KN7uxuR89w~gooMLQqB9a~K8esoIs2eW~f4V1aCLsyM~zyKU3Q5L4C~oJAJo4VO5E~eVxus64GZU~pXtj42c796~7dr5yDiiNE~R1dhNf-8Dm~Ac_mADAVwx~OT4SuGenFI~EUwzYuPRbU~NpsIVvS-GF~it3ufADtig~c-0HyG_fc2~nQRrj5c6w_~pzzjRSV6ZO~JckS4u3gtG~Oa9b6mEc1T~T4PSuIdiwS~RybylJRnhJ~Gx02furCtC~QKSUyLo4US~kP7msdIeEU~Ce-EdaHA-3~sQC4pGQx9E~e4ea3ikQSl~bFcHQpe7ZU~cFXtS-flQO~ueeKYaEKwj~tgP8r-gOe_~ThlAk1fdQu~65aiw_5Y72~xZ6jtQjaj9~PwDMGzD6xn~Qpck2xl8b8~mFuvKdN_Mu~T53qL7THLZ~ETjPkL0e6r~J92A0HwTlq~2_IEt5mZob~4Ew9pzGr3u~WcTW9TCOx9~Bd2L9ZBE8q~fg8EOt4owo~jEoxuA2PIS~ITqZ5UzdOC~WBGCipQh65~aNqTPYQ7NR~b3tIEUsHql~aUKGRzPd6e~YmvrRNXF4U~qs1FGS26bJ~m3EJRa33xU~LJo91uBPz4~n7YxiukgPF~-sp-9oh8uv~qNNBETb79P~7H3YOcbzOl~nKtPXE_Xot~E3tEXRxts5~RjyWcTb8JF~faHcYIP1U0~gVfGX_rH_Y~VFCsNMKQI1; __utmb=235335808.16.9.1568563151660',
            'dnt': '1',
            'referer': 'https://www.pixiv.net/',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
        }

    def get_list(self):
        response = requests.get(self.ajax_url.format(i), headers=self.headers)
        json_data = response.json()
        list_temp = json_data['body']
        for l in list_temp:
            url_tamp = l['urls']['original']
            yield url_tamp
            # with open('pixiv.json', 'a', encoding='utf-8') as f:
            #     f.write(url_tamp + '\n')
            # 导出

    def get_img(self, url):
        if not os.path.isdir('./img'):
            os.makedirs('./img')
        file_name = re.findall('/\d+/\d+/\d+/\d+/\d+/\d+/(.*)', url)[0]
        if os.path.isfile(f'./img/{file_name}'):
            print(f'{file_name}已存在！')
            return 1
        print(f'开始下载：{file_name}')
        t = 0
        while t < 3:
            try:
                img_temp = requests.get(url, headers=self.headers, timeout=15)
                break
            except requests.exceptions.ConnectTimeout:
                print("连接超时！正在重试！")
                t += 1
        with open(f'./img/{file_name}', 'wb') as fp:
            fp.write(img_temp.content)


if __name__ == '__main__':
    i = '41995642'  # 接口 图片PID
    pixiv = PixivSpider()
    for id_url in pixiv.get_list():
        pixiv.get_img(id_url)
