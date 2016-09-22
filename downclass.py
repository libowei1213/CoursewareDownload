# -*- coding:utf-8 -*-
import requests
import re
from bs4 import BeautifulSoup
import os


# 下载课件
def download(url, fileName, className, session):
    dir = os.getcwd() + "/" + className
    file = os.getcwd() + "/" + className + "/" + fileName
    
    # 没有课程文件夹则创建
    if not os.path.exists(dir):
        os.mkdir(dir)
    # 存在该文件，返回
    if os.path.exists(file):
        print(fileName + u"已存在，就不下载了")
        return
    print(u"开始下载" + fileName + u"...")
    s = session.get(url)
    with open(file, "wb") as data:
        data.write(s.content)
    



if __name__ == '__main__':
    
    print("====================")
    print("课件自动下载脚本 v0.1")
    print("by libowei")
    print("====================")
    print("\n")
    
    
    try:
        config = open("user.config")
    except IOError:
        print("请创建user.config文件")
        exit()
        
    line = config.readline().split(" ", 2)
    username = line[0]
    password = line[1]
    
    
    print(u"您的登录名为：" + username)
    flag = raw_input("是否继续?(y/n)")
    if flag != "Y" and flag != "y":
        exit()
    
    try:
    
        session = requests.Session()
        s = session.get("http://sep.ucas.ac.cn/slogin?userName=" + username + "&pwd=" + password + "&sb=sb&rememberMe=1");
        bsObj = BeautifulSoup(s.text, "html.parser")
        nameTag = bsObj.find("li", {"class":"btnav-info", "title":"当前用户所在单位"})
        name = nameTag.get_text().encode("utf-8")
        # 正则提取出 单位 姓名
        # 这个正则还有问题
        match = re.compile(r"\s+(.+)\s+(.+)\s+(.+)").match(name)
        if(match):
            print("登录成功,欢迎 " + match.group(3))
        else:
            print("登录失败，请核对用户名密码重启软件")
            exit()
        
        
        print("获取信息中，稍安勿躁....")
    
        # 课程网站
        s = session.get("http://sep.ucas.ac.cn/portal/site/16/801")
        bsObj = BeautifulSoup(s.text, "html.parser")
        
        newUrl = bsObj.find("noscript").meta.get("content")[6:]
        s = session.get((newUrl))
        bsObj = BeautifulSoup(s.text, "html.parser")
        newUrl = "http://course.ucas.ac.cn" + bsObj.find("frameset").findAll("frame")[0].get("src")
        s = session.get(newUrl)
        bsObj = BeautifulSoup(s.text, "html.parser").find("a", {"class":"icon-sakai-membership"})
        newUrl = bsObj.get("href")
        # 进入我的课程页面
        s = session.get(newUrl)
        newUrl = BeautifulSoup(s.text, "html.parser").find("iframe").get("src");
        # 进入课程列表
        s = session.get(newUrl)
        # 读取所有课程
        classList = []
        trList = BeautifulSoup(s.text, "html.parser").findAll("tr")
        # 去掉第一行
        del trList[0]
        for tr in trList:
            tdList = tr.findAll("td")
            className = tdList[2].get_text().strip()  # 课程名
            classId = tdList[0].get_text().strip()  # 课程id
            classWebsite = tdList[2].h4.a.get("href")  # 课程url
            classTeacher = tdList[3].get_text().strip()  # 课程老师
            classList.append((classId, className, classWebsite, classTeacher));
        print("您已选" + str(len(classList)) + "门课：")
        for c in classList:
            print(c[1] + "(" + c[3] + ")")
        for c in classList:
            url = c[2]
            s = session.get(url)
            # 资源url
            url = BeautifulSoup(s.text, "html.parser").find("a", {"class", "icon-sakai-resources"}).get("href")
            s = session.get(url)
            url = BeautifulSoup(s.text, "html.parser").find("iframe").get("src")
            s = session.get(url)
            resourceList = BeautifulSoup(s.text, "html.parser").findAll("tr")
            # 删除0 1 和最后一个元素
            resourceList.pop()
            del resourceList[0]
            del resourceList[0]
            if len(resourceList) <= 0:
                print (u"课程" + c[1] + u"没有课件")
            else:
                print (u"课程" + c[1] + u"有" + str(len(resourceList)) + u"个课件")
                for res in resourceList:
                    resName = res.findAll("td")[2].get_text().strip()
                    resUrl = res.a.get("href")
                    download(resUrl, resName, c[1], session)
    except Exception:
        print("妈呀，出错了，请重启软件重试")
        exit()
                
                
                
                
            

    
