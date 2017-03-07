# -*- coding:utf8 -*-
import requests
import re
from bs4 import BeautifulSoup
import os
import sys
import json


# 下载课件
def download(url, fileName, className, session):
    dir = os.getcwd() + "/" + className
    file = os.getcwd() + "/" + className + "/" + fileName
    # 没有课程文件夹则创建
    if not os.path.exists(dir):
        os.mkdir(dir)
    # 存在该文件，返回
    if os.path.exists(file):
        print(fileName + "已存在，就不下载了")
        return
    print("开始下载" + fileName + u"...")
    s = session.get(url)
    with open(file, "wb") as data:
        data.write(s.content)


def errorExit(msg):
    print(msg)
    os.system("pause")
    exit()


def getClass(currentClass, url, session, data):
    if data != None:
        s = session.post(url, data=data)
    else:
        s = session.get(url)
    resourceList = BeautifulSoup(s.text, "html.parser").findAll("tr")

    for res in resourceList:
        if res.find("td") == None:
            continue
        if res.find("h4") == None:
            continue

        resUrl = res.find("h4").a.get("href")

        # 文件夹
        if res.find("h4").a.get("title") == "打开此文件夹":
            path = res.find("td", {"headers": "checkboxes"}).input.get("value")
            data = {'source': '0', 'collectionId': path, 'navRoot': '', 'criteria': '', 'sakai_action': 'doNavigate',
                    'rt_action': '', 'selectedItemId': '', 'resourceName': ''}
            # print (path)
            urlNew = BeautifulSoup(s.text, "html.parser").find("form").get("action")
            getClass(currentClass, urlNew, session, data)
        # 有版权的文件，构造下载链接
        elif res.find("h4").a.get("href") == "#":
            jsStr = res.find("h4").a.get("onclick")
            reg = re.compile(r"openCopyrightWindow\('(.*)','copyright")
            match = reg.match(jsStr)
            if match:
                resUrl = match.group(1)
                resName = resUrl.split("/")[-1]
                download(resUrl, resName, currentClass, session)
        # 课件可以直接下载的
        else:
            resName = resUrl.split("/")[-1]
            download(resUrl, resName, currentClass, session)


if __name__ == '__main__':

    print(u"=============================")
    print(u"    课件自动下载脚本 v1.0")
    print(u"        by libowei")
    print(u"=============================")

    try:
        config = open("user.txt", encoding='utf-8')
    except IOError:
        errorExit("请创建user.txt文件")

    try:
        line = config.readline().split()
        username = line[0]
        password = line[1]
    except IndexError:
        errorExit("user.txt文件格式不正确啊")

    print("您的登录名为：" + username)
    flag = input("是否继续？(y/n)")
    if flag != "Y" and flag != "y":
        exit()
    try:
        session = requests.Session()

        session.get("http://onestop.ucas.ac.cn/home/index")
        post = {'username': username, 'password': password, 'remember': 'checked'}
        headers = {'Host': 'onestop.ucas.ac.cn', 'Referer': 'http://onestop.ucas.ac.cn/home/index',
                   'X-Requested-With': 'XMLHttpRequest'}
        s = session.post(
            "http://onestop.ucas.ac.cn/Ajax/Login/0", data=post, headers=headers);

        if not "true" in s.text:
            if "false" in s.text:
                errorExit(json.loads(s.text)['msg'])
            else:
                errorExit(s.text)

        url = json.loads(s.text)['msg']
        s = session.get(url)

        bsObj = BeautifulSoup(s.text, "html.parser")
        nameTag = bsObj.find("li", {"class": "btnav-info", "title": "当前用户所在单位"})
        if nameTag == None:
            errorExit("登录失败，请核对用户名密码、验证码")
        name = nameTag.get_text()
        # 正则提取出 姓名 （单位还是提取不出来啊 不知道为啥）
        match = re.compile(r"\s*(\S*)\s*(\S*)\s*").match(name)
        print("\n")
        if (match):
            name = match.group(2)
            print("欢迎您," + name)
        else:
            errorExit("登录失败，请核对用户名密码重启软件")
        print(u"......................")
        print(u"获取信息中，稍安勿躁....")
        print(u"......................")

        # 课程网站
        s = session.get("http://sep.ucas.ac.cn/portal/site/16/801")
        bsObj = BeautifulSoup(s.text, "html.parser")

        newUrl = bsObj.find("noscript").meta.get("content")[6:]
        s = session.get((newUrl))
        bsObj = BeautifulSoup(s.text, "html.parser")
        newUrl = "http://course.ucas.ac.cn" + bsObj.find("frameset").findAll("frame")[0].get("src")
        s = session.get(newUrl)
        bsObj = BeautifulSoup(s.text, "html.parser").find("a", {"class": "icon-sakai-membership"})
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
        # 打印所有课程
        for c in classList:
            print(c[1] + "(" + c[3] + ")")

        downloadClassList = []
        # 下载指定课程的课件
        if len(sys.argv) > 1:
            selectedClass = sys.argv[1]
            for c in classList:
                if selectedClass in c[1] or selectedClass in c[0] or selectedClass in c[3]:
                    downloadClassList.append(c)
        if len(downloadClassList) > 0:
            classList = downloadClassList[:]
            print("\n将要下载以下课程：\n%s" % ("\n".join([c[1] for c in classList])))

        print("\n")
        print("开始下载课件......")
        for c in classList:
            url = c[2]
            s = session.get(url)
            # 资源url
            url = BeautifulSoup(s.text, "html.parser").find("a", {"class", "icon-sakai-resources"}).get("href")
            s = session.get(url)
            url = BeautifulSoup(s.text, "html.parser").find("iframe").get("src")
            getClass(c[1], url, session, None)
    except Exception:
        errorExit("妈呀，出错了，请重启软件重试")

    print("\n")
    os.remove("captcha.png")
    errorExit("课件下好了，滚去学习吧！\n")
