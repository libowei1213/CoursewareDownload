# coding=utf-8

from requests_html import HTMLSession
import re
import os
import sys
import json
import time


# 下载课件
def download(url, fileName, className, session):
    # \xa0转gbk会有错
    fileName = fileName.replace(u"\xa0", " ").replace(u"\xc2", "")

    dir = os.path.join(os.getcwd(), className)
    file = os.path.join(dir, fileName)
    # 没有课程文件夹则创建
    if not os.path.exists(dir):
        os.makedirs(dir)
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
        r = session.post(url, data=data)
    else:
        r = session.get(url)

    resourceList = r.html.find("tr")

    for res in resourceList[2:]:
        resUrl = res.find("a", first=True).attrs.get("href")
        # 文件夹
        if res.find("a", first=True).attrs.get("title") == "打开此文件夹":
            path = res.find("a", first=True).attrs.get("onclick")
            reg = re.compile("Id'\).value='([\s\S]*)';document")
            match = reg.search(path)
            if match:
                path = match.group(1)

                reg = re.compile('name="sakai_csrf_token" value="(.*)"')
                sakai_csrf_token = reg.search(r.text).group(1)
                data = {'source': '0',
                        'collectionId': path,
                        'navRoot': '',
                        'criteria': 'title',
                        'sakai_action': 'doNavigate',
                        'rt_action': '',
                        'selectedItemId': '',
                        'itemHidden': "false",
                        'itemCanRevise': 'false',
                        'sakai_csrf_token': sakai_csrf_token
                        }
                urlNew = r.html.find("form", first=True).attrs.get("action")
                dirName = res.find("span.hidden-sm", first=True).text.strip()
                dirName = re.sub(r"[/\\:*\"<>|?]", "", dirName)
                dirName = os.path.join(currentClass, dirName)
                getClass(dirName, urlNew, session, data)
        # 有版权的文件，构造下载链接
        elif res.find("a", first=True).attrs.get("href") == "#":
            jsStr = res.find("a", first=True).attrs.get("onclick")
            reg = re.compile(r"openCopyrightWindow\('(.*)','copyright")
            match = reg.match(jsStr)
            if match:
                resUrl = match.group(1)
                path = re.sub("http://course.ucas.ac.cn/access", "", resUrl)
                resName = res.find("a")[1].text.replace("©", "").strip()
                resName = re.sub(r"[/\\:*\"<>|?]", "", resName)
                resUrl = "http://course.ucas.ac.cn/access/accept?ref=%s&url=%s" % (path, path)
                download(resUrl, resName, currentClass, session)
        # 课件可以直接下载的
        else:
            resName = res.find("span.hidden-sm", first=True).text.strip()
            resName = re.sub(r"[/\\:*\"<>|?]", "", resName)
            if "." not in resName:
                resName += (".%s" % resUrl.split(".")[-1])
            download(resUrl, resName, currentClass, session)


def getClassList(session):
    filename = "classes.txt"

    if os.path.exists(filename):
        # 课程列表文件更新时间大于十天，重新下载
        timestamp = os.path.getmtime(filename)
        if time.time() - timestamp < 10 * 24 * 3600:
            return
        else:
            os.remove(filename)

    print("下载课程列表中....\n")

    r = session.get("http://sep.ucas.ac.cn/portal/site/226/821")

    url = r.html.find("noscript", first=True).find("meta", first=True).attrs.get("content")[6:]
    r = session.get(url)

    terms = {}
    r = session.get('http://jwxk.ucas.ac.cn/course/termSchedule')
    options = r.html.find("select[name=termId]", first=True).find("option")[:3]
    for option in options:
        terms[option.attrs.get("value")] = option.text

    classList = []
    for termId, termName in terms.items():
        post = {'termId': termId, 'courseAttribute': '', 'isSummer': ''}
        r = session.post('http://jwxk.ucas.ac.cn/course/termSchedule', data=post)
        trs = r.html.find("tbody", first=True).find("tr")

        for tr in trs:
            tds = tr.find("td")
            if len(tds) < 5: continue
            no = tds[1].find("a", first=True).attrs.get("href")[19:]
            id = tds[1].text
            name = tds[2].text
            teacher = tds[14].text
            classList.append("%s|%s|%s|%s|%s\n" % (no, id, name, teacher, termName))

    with open("classes.txt", "w", encoding="utf-8") as file:
        file.writelines(classList)


def readClassList():
    classList = []
    with open("classes.txt", encoding="utf-8") as file:
        for line in file:
            classList.append(tuple(line.split('|')))
    return classList


def addCourseSite(session, ids):
    for id in ids:
        r = session.get("http://sep.ucas.ac.cn/portal/site/226/821")
        url = r.html.find("noscript", first=True).find("meta", first=True).attrs.get("content")[6:]
        r = session.get(url)
        r = session.get("http://jwxk.ucas.ac.cn/courseManage/addCourseSite.json?courseId=%s&_=%s" % (id, time.time()))
        if not "加入课程网站成功" in r.text:
            return r.text
    return 1


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
        session = HTMLSession()
        session.get("http://onestop.ucas.ac.cn/home/index")
        post = {'username': username, 'password': password, 'remember': 'checked'}
        headers = {'Host': 'onestop.ucas.ac.cn',
                   'Referer': 'http://onestop.ucas.ac.cn/home/index',
                   'X-Requested-With': 'XMLHttpRequest',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'
                   }
        r = session.post(
            "http://onestop.ucas.ac.cn/Ajax/Login/0", data=post, headers=headers)

        if not "true" in r.text:
            if "false" in r.text:
                errorExit(json.loads(r.text)['msg'])
            else:
                errorExit(r.text)

        url = json.loads(r.text)['msg']
        r = session.get(url)

        nameTag = r.html.find("li.btnav-info[title=当前用户所在单位]", first=True)
        if nameTag == None:
            errorExit("登录失败，请核对用户名密码、验证码")
        name = nameTag.text
        # 正则提取出 姓名 （单位还是提取不出来啊 不知道为啥）
        match = re.compile(r"\s*(\S*)\s*(\S*)\s*").match(name)
        print("\n")
        if (match):
            org = match.group(1).replace("\xc2", "").replace("\x80", "").replace("\x90", "").strip()
            name = match.group(2).replace("\xc2", "").replace("\x80", "").replace("\x90", "").strip()
            print("欢迎您！%s，%s" % (org, name))
        else:
            errorExit("登录失败，请核对用户名密码重启软件")
        print("......................")
        print("获取信息中，稍安勿躁....")
        print("......................")

        # 根据参数判断 是否为加入课程网站
        if len(sys.argv) > 2:
            if sys.argv[1] == "add":
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
                        print("%s %s %s %s %s" % (c[0], c[1], c[2], c[3], c[4]))
                        classNo.append(c[0])
                    result = input("\n请输入要加入课程网站的课程的数字id（可用逗号分隔）：")
                    if "," in result:
                        result = result.split(",")
                    else:
                        result = [result]

                    for id in result:
                        if id not in classNo:
                            errorExit("输入错误！\n")

                    flag = addCourseSite(session, result)
                    if flag == 1:
                        errorExit("%s个课程加入课程网站成功\n" % len(result))
                    else:
                        errorExit(flag)

                # 待选课程为1 直接加入课程网站
                else:
                    flag = addCourseSite(session, [addClassList[0][0]])
                    if flag == 1:
                        errorExit("%s 加入课程网站成功\n" % addClassList[0][2])
                    else:
                        errorExit(flag)
            else:
                errorExit("输入参数错误")

        # 课程网站
        r = session.get("http://sep.ucas.ac.cn/portal/site/16/801")

        newUrl = r.html.find("noscript", first=True).find("meta", first=True).attrs.get("content")[6:]
        # http://course.ucas.ac.cn/portal/plogin?Identity=fd86ee9b-3e45-4e5f-9bd1-5647c652221f&roleId=801
        r = session.get(newUrl)

        newUrl = r.html.find("a#allSites", first=True).attrs.get("href")
        # 右上角“我的课程”->查看所有课程
        # http://course.ucas.ac.cn/portal/site/%7E201628018629055/tool-reset/7047982f-9573-4de6-ab03-8357bdb1ef53
        r = session.get(newUrl)
        # hidden
        sakai_csrf_token = r.html.find("input[name=sakai_csrf_token]", first=True).attrs.get("value")
        post = {
            "eventSubmit_doChange_pagesize": "changepagesize",
            "selectPageSize": 200,
            "sakai_csrf_token": sakai_csrf_token
        }
        # http://course.ucas.ac.cn/portal/site/~201628018629055/tool/7047982f-9573-4de6-ab03-8357bdb1ef53
        # 每页显示200个课程
        newUrl = re.sub("-reset", "", newUrl)
        r = session.post(newUrl, data=post)

        titles = r.html.find("td[headers=title]")
        # 课程列表 去掉第一行
        # 读取所有课程
        classList = []
        for title in titles[1:]:
            className = title.text.strip()
            className = re.sub(r"[/\\:*\"<>|?]", "", className)
            classId = title.find("a.getSiteDesc", first=True).attrs.get("id")
            classWebsite = title.find("a", first=True).attrs.get("href")
            classList.append((classId, className, classWebsite))

        print("您已选%s门课：" % str(len(classList)))
        # 打印所有课程
        for c in classList:
            print(c[1])

        downloadClassList = []
        # 下载指定课程的课件
        if len(sys.argv) > 1:
            selectedClass = sys.argv[1]
            for c in classList:
                if selectedClass in c[1] or selectedClass in c[0]:
                    downloadClassList.append(c)
        if len(downloadClassList) > 0:
            classList = downloadClassList[:]
            print("\n将要下载以下课程：\n%s" % ("\n".join([c[1] for c in classList])))

        print("\n")
        print("开始下载课件......")
        for c in classList:
            url = c[2]
            r = session.get(url)
            # 左侧菜单栏 第4个 ”资源“
            url = r.html.find("a.Mrphs-toolsNav__menuitem--link")[3].attrs.get("href")
            print("\n=====%s=====" % c[1])
            getClass(c[1], url, session, None)
    except NameError as e:
        errorExit("妈呀，出错了，错误信息: %s" % e)

    print("\n")
    errorExit("课件下好了，滚去学习吧！\n")
