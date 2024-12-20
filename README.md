**一个Pixiv小爬虫，目前只可以爬每日， 支持长时间爬取 跳过已经爬过的**

![HapiGo_2024-12-20_12.39.49.png](https://img.nyaasuki.com/2024/12/20/6764f51f5fccf.png)

## 环境需求

Python:3.8+ / Redis

## 食用方法

**Linux/OSX:**

```shell
git clone https://github.com/nyaasuki/PixivSpider.git && cd ./PixivSpider
python3 main.py
```

**Windows:**

1. 下载/clone这个项目

2. 配置好环境（python、Redis）

3. 打开你的CMD窗口

4. 输入python+‘ ’    ←这是一个空格

5. 用鼠标把**main.py**这个文件拖到cmd窗口

   ​	^_^

## 注意事项

1.requests安装错误

`ERROR: Could not find a version that satisfies the requirement resquests
ERROR: No matching distribution found for resquests`

解决方案：手动安装requests

'pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests'

2.请输入一个cookie

目前此项留空直接回车也可以正常爬取（匿名模式），如果后续添加新功能可能需要

此项储存在本地redis中

3.错误：无法连接到Redis服务，请确保Redis服务正在运行
项目使用redis查重 需要安装redis 
官方安装教程：https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/

## 特别提醒

正常来说，当没有出现上方问题时，程序出现问题大多为你的上网方式不够科学
缓慢更新中...
