import os
import requests
from selenium import webdriver
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#from selenium.webdriver.common.proxy import ProxyType
from bs4 import BeautifulSoup
from random import choice
import threading
from queue import Queue
from PIL import Image
from io import BytesIO
from time import sleep
import getpass

# Pixiv爬虫
class PixivSpider(object):

    # 功能：构造函数
    # 参数：username 用户名；password 密码
    # 返回值：无
    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.ses = requests.session()
        self.uas = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]
        self.proxies = {  # pixiv被墙了，要翻墙
            'http': 'http://127.0.0.1:1080',
            'https': 'https://127.0.0.1:1080',
        }
        self.ses.proxies = self.proxies

        self.driver = self.init_driver()

        self.root_url = 'https://www.pixiv.net/'
        self.login_url = 'https://accounts.pixiv.net/login'
        self.search_url = os.path.join(self.root_url, 'search.php')
        self.painter_info_url = os.path.join(self.root_url, 'member.php')
        self.painter_imgs_url = os.path.join(self.root_url, 'member_illust.php')
        self.bookmark_url = os.path.join(self.root_url, 'bookmark.php')

        self.root_path = r'F:\xxcc\program\python\projects\pixiv-spider'
        self.save_path = os.path.join(self.root_path, 'data')

        self.q = Queue()
        self.lock = threading.Lock()
        self.th_cnt = 0
        self.ths = []
        self.stop = False

        self.success_cnt = 0
        self.dirname = None
        self.hot = 0

    # 功能：去除字符串中的不合法字符
    # 参数：原字符串
    # 返回值：处理后的字符串
    @staticmethod
    def clean_str(string):
        string = string.strip()
        for char in r'\/:*?"<>|':
            string = string.replace(char, '_')
        return string

    # 功能：初始化浏览器
    # 参数：无
    # 返回值：driver
    def init_driver(self):
        '''
        desired_capabilities = DesiredCapabilities.PHANTOMJS.copy()
        desired_capabilities["phantomjs.page.settings.loadImages"] = False
        desired_capabilities["phantomjs.page.settings.userAgent"] = (choice(self.uas))
        proxy = webdriver.Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = '127.0.0.1:1080'
        proxy.add_to_capabilities(desired_capabilities)
        driver = webdriver.PhantomJS(executable_path=r'F:\phantomjs-2.0.0-windows\bin\phantomjs.exe')
        driver.start_session(desired_capabilities)
        '''
        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument('--proxy-server=127.0.0.1:1080')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get('http://1212.ip138.com/ic.asp')
        driver.maximize_window()
        return driver

    # 功能：初始化线程
    # 参数：无
    # 返回值：无
    def init_threads(self):
        self.ths = []
        self.stop = False
        for i in range(self.th_cnt):
            self.ths.append(threading.Thread(target=self.download_thread, args=(), name=str(i)))
            self.ths[i].daemon = True
            self.ths[i].start()

    # 功能：等待所有线程结束
    # 参数：无
    # 返回值：无
    def wait_threads(self):
        self.stop = True
        for thread in self.ths:
            thread.join()
        print('所有线程结束')

    # 功能：用requests发送get请求
    # 参数：url 目标网址；headers 请求头；params get的参数
    # 返回值：请求的响应
    def send_get(self, url, headers=None, params=None):
        if not headers:
            headers = {}
        headers['User-Agent'] = choice(self.uas)
        for cnt in range(5):
            try:
                if 'Refer' in headers.keys():
                    response = self.ses.get(url, headers=headers, params=params, timeout=60)
                else:
                    response = self.ses.get(url, headers=headers, params=params, timeout=20)
                return response
            except Exception as e:
                print(e)
                print('requests get {} failed; cnt = {}'.format(url, cnt + 1))
        raise TimeoutError

    # 功能：用selenium发送get请求
    # 参数：url 目标网址
    # 返回值：请求的响应
    def driver_get(self, url):
        timeout = 90
        self.driver.set_page_load_timeout(timeout)
        for cnt in range(5):
            try:
                self.driver.get(url)
                return
            except Exception as e:
                print(e)
                print('driver get {} failed; cnt = {}'.format(url, cnt + 1))
                timeout += 60
                self.driver.set_page_load_timeout(timeout)
        raise TimeoutError

    # 功能：登录
    # 参数：username 用户名；password 密码
    # 返回值：无
    def login(self):
        html = self.send_get(self.login_url).text
        print('获取postkey完毕')
        soup = BeautifulSoup(html, 'lxml')
        post_key = soup.find('input')['value']
        login_data = {
            'pixiv_id': self.username,
            'password': self.password,
            'return_to': self.root_url,
            'post_key': post_key
        }
        response = self.ses.post(self.login_url, data=login_data, headers={'User-Agent': choice(self.uas)})
        assert response.status_code == 200, '登录失败'
        print('获取cookie完毕')
        self.driver.delete_all_cookies()
        cookies = self.ses.cookies
        for cookie in dict(cookies).items():
            add_cookie = {
                'name': cookie[0],
                'value': cookie[1],
                'domain': '.pixiv.net',
                'path': '/',
                'expires': None,
            }
            self.driver.add_cookie(add_cookie)
        print('登录成功')

    # 功能：按关键词搜索图片
    # 参数：content 搜索关键词；hot 最少人气；multiple 是否下载图集；dirname 保存到的文件夹名；page_cnt 页数；
    #       h 值为-1无h，0都有，1只有h；th_cnt 线程数
    # 返回值：无
    def search(self, content, hot=0, dirname=None, page_cnt=None, h=0, th_cnt=8):
        self.success_cnt = 0
        self.hot = hot
        self.th_cnt = th_cnt
        self.init_threads()
        if hot >= 10000:
            content += ' 10000users入'
        elif hot >= 1000:
            content += ' 1000users入'
        elif hot >= 100:
            content += ' 100users入'
        if dirname is None:
            dirname = self.clean_str(content)
            if hot:
                dirname += ' hot={}'.format(hot)
        mode = ''
        if h == 1:
            dirname += ' h'
            mode = 'r18'
        if h == -1:
            dirname += ' safe'
            mode = 'safe'
        self.dirname = dirname
        dir_path = os.path.join(self.save_path, dirname)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        url = self.search_url + '?order=date_d&word={}&mode={}'.format(content, mode)
        page = 1
        while page_cnt is None or page <= page_cnt:
            print('第{}页'.format(page))
            cur_url = url + '&p={}'.format(page)
            self.driver_get(cur_url)
            if not self.parse_search(self.driver.page_source):
                break
            page = page + 1
        self.driver.quit()
        self.wait_threads()
        print('搜索完成，成功保存{}张图片'.format(self.success_cnt))

    # 功能：搜索画师作品
    # 参数：painter_id 画师id；hot 最少人气；dirname 保存到的文件夹名；page_cnt 页数；th_cnt 线程数
    # 返回值：无
    def painter_search(self, painter_id, hot=0, dirname=None, page_cnt=None, th_cnt=8):
        self.success_cnt = 0
        self.hot = hot
        self.th_cnt = th_cnt
        self.init_threads()
        soup = BeautifulSoup(self.send_get(self.painter_info_url, params={'id': painter_id}).text, 'lxml')
        if soup.find('h2', class_='error-title'):
            print('未找到该画师')
            return
        painter_name = self.clean_str(soup.find('a', class_='user-name')['title'])
        if dirname is None:
            dirname = painter_name
            if hot:
                dirname += ' hot={}'.format(hot)
        self.dirname = dirname
        dir_path = os.path.join(self.save_path, dirname)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        url = self.painter_imgs_url + '?type=illust&id={}'.format(painter_id)
        page = 1
        while page_cnt is None or page <= page_cnt:
            print('第{}页'.format(page))
            cur_url = url + '&p={}'.format(page)
            self.driver_get(cur_url)
            if not self.parse_painter_or_bookmark_search(self.driver.page_source):
                break
            page = page + 1
        self.driver.quit()
        self.wait_threads()
        print('搜索完成，成功保存{}张图片'.format(self.success_cnt))

    # 功能：批量下载收藏的作品
    # 参数：hide 是否下载私人收藏；tag 收藏的标签；th_cnt 线程数
    # 返回值：无
    def bookmark_search(self, hide=False, tag=None, th_cnt=8):
        self.success_cnt = 0
        self.hot = 0
        self.th_cnt = th_cnt
        self.init_threads()
        url = self.bookmark_url + '?'
        dirname = '收藏 ' + ('私人' if hide else '公开')
        if hide:
            url += 'rest=hide&'
        if tag:
            dirname += ' tag=' + self.clean_str(tag)
            url += 'tag={}&'.format(tag)
        self.dirname = dirname
        dir_path = os.path.join(self.save_path, dirname)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        page = 1
        while True:
            print('第{}页'.format(page))
            cur_url = url + 'p={}'.format(page)
            self.driver_get(cur_url)
            if not self.parse_painter_or_bookmark_search(self.driver.page_source):
                break
            page = page + 1
        self.driver.quit()
        self.wait_threads()
        print('搜索完成，成功保存{}张图片'.format(self.success_cnt))

    # 功能：解析搜索页面
    # 参数：html 搜索页面源码
    # 返回值：bool类型，表示此页是否有图片
    def parse_search(self, html):
        soup = BeautifulSoup(html, 'lxml')
        if soup.find('div', class_='_no-item'):
            return False
        for figure in soup.find_all('figure'):
            a = figure.div.a
            if a.find('div'):
                continue  # 图集或GIF
            title = self.clean_str(figure.figcaption.ul.li.a['title'])
            url = os.path.splitext(a.img['data-src'].replace('c/240x240/img-master', 'img-original').replace('_master1200', ''))[0]
            self.lock.acquire()
            self.q.put((title, url))
            self.lock.release()
        return True

    # 功能：解析画师作品页面或个人收藏页面
    # 参数：html 搜索页面源码
    # 返回值：bool类型，表示此页是否有图片
    def parse_painter_or_bookmark_search(self, html):
        soup = BeautifulSoup(html, 'lxml')
        if soup.find('li', class_='_no-item'):
            return False
        for li in soup.find('ul', class_='_image-items').find_all('li', class_='image-item'):
            if li.find('div', class_='page-count') or li.find('a', class_='ugoku-illust'):
                # 图集或GIF
                continue
            if self.hot:
                detail_url = os.path.join(self.root_url, li.a['href'][1:])
                if not self.check_hot(detail_url):
                    continue
            title = self.clean_str(li.find('h1', class_='title')['title'])
            url = os.path.splitext(li.a.div.img['data-src'].replace('c/150x150/img-master', 'img-original').replace('_master1200', ''))[0]
            print('发现 {} {}'.format(title, url))
            self.lock.acquire()
            self.q.put((title, url))
            self.lock.release()
        return True

    # 功能：检查图片人气是否高于指定值
    # 参数：url 图片详情页网址
    # 返回值：bool类型，表示人气是否高于指定值
    def check_hot(self, url):
        hot = int(BeautifulSoup(self.send_get(url).text, 'lxml').find('dd', class_='rated-count').get_text())
        return hot >= self.hot

    # 功能：下载图片
    # 参数：无
    # 返回值：无
    def download_thread(self):
        name = threading.current_thread().name
        while True:
            self.lock.acquire()
            if self.q.empty():
                self.lock.release()
                if self.stop:
                    break
            else:
                title, url = self.q.get()
                self.lock.release()
                print('线程{} 正在获取图片 title: {}'.format(name, title))
                types = ['.jpg', '.png']
                img_type = None
                size = 0
                err = False
                for cur_type in types:
                    cur_url = url + cur_type
                    try:
                        img = self.send_get(cur_url, headers={'Referer': self.root_url}).content
                    except:
                        err = True
                        break
                    try:
                        size = Image.open(BytesIO(img)).size
                        img_type = cur_type
                        break
                    except:
                        pass
                if err:
                    print(title, '获取失败')
                    self.lock.acquire()
                    self.q.put((title, url))
                    self.lock.release()
                    continue
                if img_type is None:
                    print(title, '找不到正确类型')
                    continue
                print('线程{} 图片获取完毕 title: {}'.format(name, title))
                if self.save_img(img, title, img_type, size):
                    print('线程{} 图片保存成功 img_name: {}{}'.format(name, title, img_type))
                    self.success_cnt += 1
                else:
                    print('线程{} 图片已存在 img_name: {}{}'.format(name, title, img_type))
        print('线程{}结束'.format(name))

    # 功能：保存图片
    # 参数：img_bytes 图片数据；title 图片标题；img_type 图片后缀；size 图片大小
    # 返回值：bool类型，若图片已存在返回False，否则返回True
    def save_img(self, img_bytes, title, img_type, size):
        filename = title + img_type
        dir_path = os.path.join(self.save_path, self.dirname)
        file_path = os.path.join(dir_path, filename)
        cnt = 0
        while os.path.exists(file_path):
            if Image.open(file_path).size == size:
                return False
            cnt += 1
            file_path = os.path.join(dir_path, '{}({}){}'.format(filename, cnt, img_type))
        with open(file_path, 'wb') as fout:
            fout.write(img_bytes)
        return True

if __name__ == '__main__':
    username = input('用户名：')
    #password = getpass.getpass(prompt='密码（不回显）：')
    password = input('密码：')
    spider = PixivSpider(username, password)
    spider.login()
    #spider.search('島風', hot=10000)
    #spider.painter_search(212801, hot=5000)
    spider.bookmark_search(hide=True, th_cnt=4)
