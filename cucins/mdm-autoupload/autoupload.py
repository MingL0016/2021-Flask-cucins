from selenium import webdriver
import os
from selenium.webdriver.support.wait import WebDriverWait
# 模拟登陆
# rep = requests.Session()
browser = webdriver.Chrome()
browser.implicitly_wait(10)  # 设置隐性等待,等待10S加载出相关控件再执行之后的操作
browser.maximize_window()
browser.get('http://127.0.0.1:5000/reloginpage')
# 输入用户名
username = browser.find_element_by_xpath('//*[@id="username"]')
username.clear()
username.send_keys('madongmei')
print('username input success')
# 输入密码
browser.find_element_by_xpath('//*[@id="password"]').send_keys('madongmei')
print('password input success')
# 点击登陆
browser.find_element_by_xpath('//*[@id="submit"]').click()
print('login success')
# 切换到个人主页
browser.current_window_handle
browser.find_element_by_xpath('/html/body/nav/div/div/a[3]').click()
# 切换到当前窗口
browser.current_window_handle
# 上传部分
# 获取当前目录，并将data文件夹路径附在其后
dir = os.getcwd()+"\\images\\"
# 读取文件夹中文件
pics = os.listdir(dir)
print(os.getcwd())
print(pics)
flag = 100
for pic in pics:
    i = 0
    path = dir+pic
    # 将文件传入接口
    temp = browser.find_element_by_xpath(
        "/html/body/div/article/header/div[2]/div/span/form/input").send_keys(path)
    browser.current_window_handle
    i+1
    if i == 100:
        break
