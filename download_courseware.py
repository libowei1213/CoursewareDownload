#coding=utf-8

import requests
import re
from bs4 import BeautifulSoup
import os
import sys
import json
import time
import pdb

# 下载课件
def download(url, fileName, className, session):
    # \xa0转gbk会有错
    fileName = fileName.replace(u"\xa0"," ").replace(u"\xc2","")
    dir = os.getcwd() + "/" + className
    file = os.getcwd() + "/" + className + "/" + fileName
    # 没有课程文件夹则创建
    if not os.path.exists(dir):
        os.mkdir(dir)
    # 存在该文件，返回
    if os.path.exists(file):
        print("%s已存在，就不下载了" % fileName)
        return
    print("开始下载%s..." % fileName)
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


def getClassList(session):
    print("下载课程列表中....\n")

    s = session.get("http://sep.ucas.ac.cn/portal/site/226/821")
    bsObj = BeautifulSoup(s.text, "html.parser")

    url = bsObj.find("noscript").meta.get("content")[6:]
    s = session.get(url)
	
    classList = []
    termsId=['49346','49345','49344']
    for term in termsId:
        post={'termId':term,'courseAttribute':'','isSummer':''}
        s = session.post('http://jwxk.ucas.ac.cn/course/termSchedule',data=post)
        bsObj = BeautifulSoup(s.text, "html.parser")
    
        for tr in bsObj.find("tbody").findAll("tr"):
            tds = tr.findAll("td")
            if len(tds) < 5: continue
            no = tds[1].a.get("href")[19:]
            id = tds[1].get_text()
            name = tds[2].get_text()
            classList.append("%s|%s|%s\n" % (no, id, name))

    with open("classes.txt", "w", encoding="utf-8") as file:
        file.writelines(classList)


def readClassList():
    classList = []
    with open("classes.txt", encoding="utf-8") as file:
        for line in file:
            classList.append(tuple(line.split('|')))
    return classList


def addCourseSite(session, id):
    s = session.get("http://sep.ucas.ac.cn/portal/site/226/821")
    bsObj = BeautifulSoup(s.text, "html.parser")

    url = bsObj.find("noscript").meta.get("content")[6:]
    s = session.get(url)

    s = session.get("http://jwxk.ucas.ac.cn/courseManage/addCourseSite.json?courseId=%s&_=%s" % (id, time.time()))
    if "加入课程网站成功" in s.text:
        return 1
    else:
        return s.text


if __name__ == '__main__':

    print("=============================")
    print("    课件自动下载脚本 v2.0")
    print("        by libowei")
    print("=============================")

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

    print("您的登录名为：%s" % username)
    flag = input("是否继续？(y/n)")
    if flag != "Y" and flag != "y":
        exit()
    try:
        session = requests.Session()
        session.get("http://onestop.ucas.ac.cn/home/index")
        post = {'username': username, 'password': password, 'remember': 'checked'}
        headers = {'Host': 'onestop.ucas.ac.cn',
                   'Referer': 'http://onestop.ucas.ac.cn/home/index',
                   'X-Requested-With': 'XMLHttpRequest',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'
                   }
        s = session.post(
            "http://onestop.ucas.ac.cn/Ajax/Login/0", data=post, headers=headers);

        # print(s.text)

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
            org = match.group(1).replace("\xc2","").replace("\x80","").replace("\x90","").strip()
            name = match.group(2).replace("\xc2","").replace("\x80","").replace("\x90","").strip()
            print("欢迎您！%s，%s" % (org,name))
        else:
            errorExit("登录失败，请核对用户名密码重启软件")
        print("......................")
        print("获取信息中，稍安勿躁....")
        print("......................")

        # 根据参数判断 是否为加入课程网站
        if len(sys.argv) > 2:
            if sys.argv[1] == "add":
                # 不存在课程列表文件 则获取课程列表
                if not os.path.exists("classes.txt"):
                    getClassList(session)
                classStr = sys.argv[2]
                classList = readClassList()
                addClassList = []
                for c in classList:
                    if classStr == c[0] or classStr == c[1] or classStr in c[2]:
                        addClassList.append(c)

                # 输入的课程不在课表中
                if len(addClassList) <= 0:
                    errorExit("本学期没有这门课啊！")
                # 待选课程多于1个，需要用户选择一个
                elif len(addClassList) > 1:
                    print("找到%d门课：\n" % len(addClassList))
                    classNo = []
                    for c in addClassList:
                        print("%s %s %s" % (c[0], c[1], c[2]))
                        classNo.append(c[0])
                    result = input("\n请输入要加入课程网站的课程的数字id：")
                    if result in classNo:
                        flag = addCourseSite(session, result)
                        if flag == 1:
                            errorExit("加入课程网站成功\n")
                        else:
                            errorExit(flag)
                    else:
                        errorExit("输入错误！\n")
                # 待选课程为1 直接加入课程网站
                else:
                    flag = addCourseSite(session, addClassList[0][0])
                    if flag == 1:
                        errorExit("加入课程网站成功\n")
                    else:
                        errorExit(flag)
            else:
                errorExit("输入参数错误")

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
        print("您已选%s门课：" % str(len(classList)))
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
    except Exception as e:
        errorExit("妈呀，出错了，错误信息: %s" % e)

    print("\n")
    errorExit("课件下好了，滚去学习吧！\n")