**一个Pixiv小爬虫，目前只可以爬每日，需要自己输入cookie 支持长时间爬取 跳过已经爬过的**

## 环境需求

Python:3.6+ / Redis

## 食用方法

**Linux/OSX:**

```shell
git clone https://github.com/nyaasuki/PixivSpider.git && cd ./PixivSpider
python3 Pixiv.py
```

**Windows:**

1. 下载/clone这个项目

2. 配置好环境（python、Redis）

3. 打开你的CMD窗口

4. 输入python+‘ ’    ←这是一个空格

5. 用鼠标把**Pixiv.py**这个文件拖到cmd窗口

   ​	^_^

## 注意事项

1.requests安装错误

`ERROR: Could not find a version that satisfies the requirement resquests
ERROR: No matching distribution found for resquests`

解决方案：手动安装requests

'pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests'

2.请输入一个cookie

目前此项留空直接回车也可以正常爬取，如果后续添加新功能可以能需要

此项储存在本地redis中

## 特别提醒

请开启你的扶墙 and 全局代理模式
缓慢更新中...