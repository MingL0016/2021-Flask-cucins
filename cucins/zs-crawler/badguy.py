import os
import time
import re
import requests
from tqdm import tqdm  #进度条
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from selenium import webdriver
save_folder = '.\images\\'
# 模拟登陆
browser = webdriver.Chrome()
browser.implicitly_wait(10) # 设置隐性等待,等待10S加载出相关控件再执行之后的操作
browser.maximize_window()
browser.get('http://192.168.3.49:5000/reloginpage')
# 输入用户名
username = browser.find_element_by_xpath('//*[@id="username"]')
username.clear()
username.send_keys('zhangsan')
print('username input success')
# 输入密码
browser.find_element_by_xpath('//*[@id="password"]').send_keys('badguy')
print('password input success')
# 点击登陆
browser.find_element_by_xpath('//*[@id="submit"]').click()
print('login success')
browser.current_window_handle
browser.get("http://192.168.3.49:5000/profile/11/")
browser.current_window_handle
soup = BeautifulSoup(browser.page_source, "html.parser")
#提取html中共有多少张图片，计算出应点击多少次“更多”
num=soup.select("p")
amount=int(re.findall(r"\d+",str(num[0]))[0])
times=int(amount/30)
for i in range(times):
    browser.find_element_by_xpath('//a[@class="_oidfu"]').click()
    time.sleep(1)
#对完全展开的网页进行抓取
real_html = BeautifulSoup(browser.page_source, "html.parser")
print(real_html)
srcs=[]
#匹配图片所在div块
div=real_html.select("div.img-box")
for mem in div:
    #记录图片对应的url
    srcs.append(mem.find("img")['src'])
for src in tqdm(srcs):
    file = save_folder + src.split('?')[0].split('/')[-1] # 保存本地的路径
    r = requests.get(src)  #根据文件的大小，这一步为主要耗时步骤
    #保存在本地
    with open(file, "wb") as code:
        code.write(r.content)
print('download completed')
    