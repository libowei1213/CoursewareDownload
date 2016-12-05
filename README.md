# 国科大课件下载脚本
## 简介
使用教务系统账号、密码登录课程网站，读取选课信息，从所选课程的“讲义课件”中下载该课程的课件

## 脚本功能
1. 自动登录课程网站，获取你所选课程列表
2. 在脚本当前目录下建立以课程名命名的文件夹，下载课件到相应文件夹中
3. 根据文件名判断课件是否已经下载，如课件已存在，则不进行下载
4. 可指定课程名称/课程编号/教师，下载相应的课件

## 脚本使用
### Windows控制台下执行脚本

脚本运行环境：python3.x

需要requests和bs4库，可用pip安装
```
pip install requests
pip install bs4
```

在脚本所在目录新建`user.txt`文件，将第一行改为你的登录名和密码（以空格分隔）

在脚本所在目录按shift键+鼠标右键，选择"在此处打开命令窗口"，执行命令：
```
python download_courseware.py
```

可指定课程进行下载
```
python download_courseware.py 信息检索  #下载课程名包含"信息检索"的课程的课件
python download_courseware.py 201M4006H #下载课程编号为201M4006H的课程的课件
python download_courseware.py 王斌    #下载王斌老师的课程的课件
python download_courseware.py   #不加参数，下载全部课件
```

### 运行exe可执行文件
可下载`download_courseware.exe`文件


在`download_courseware.exe`所在目录新建`user.txt`文件，将第一行改为你的登录名和密码（以空格分隔）


双击运行程序 

## 更新日志
- 2016.11.28 有些课件有“版权限制下载警告”的提示，如*091M5026H 并发数据与多核编程*的部分ppt，不能直接下载，导致脚本死循环，已修复
- 2016.12.05 新增：可下载指定课程名称/课程id/教师的课件