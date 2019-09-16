import urllib.request as urllib2
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
import time,os
import threading,threadpool
import re
import json

def strQ2B(ustring):
    """全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:                              #全角空格直接转换            
            inside_code = 32 
        elif (inside_code >= 65281 and inside_code <= 65374): #全角字符（除空格）根据关系转化
            inside_code -= 65248
        rstring += chr(inside_code)
    return rstring
    
def strB2Q(ustring):
    """半角转全角"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 32:                                 #半角空格直接转化                  
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:        #半角字符（除空格）根据关系转化
            inside_code += 65248

        rstring += chr(inside_code)
    return rstring

Type1TranslateSearcher=re.compile(r"var translate = (.*?});", re.MULTILINE | re.DOTALL)

# 根据各级菜单创建目录
def mkdir(path):
	folder = os.path.exists(path)
	if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
		os.makedirs(path)            #makedirs 创建文件时如果路径不存在会创建这个路径

def CheckType(node):
    if node.find('audio',attrs={'id':'audio'})!=None and node.find('div',attrs={'id':'article'}) and len(Type1TranslateSearcher.findall(node.text))>0:
        return 1

    return 0


Pool = threadpool.ThreadPool(10)

# 首先获取1级菜单,并对其解析从中获取2级菜单
jar = requests.cookies.RequestsCookieJar()
jar.set('.web_cookie', '33903D70378964A0D585BA8F50724B4912D16878F3D0BE8D492AAE997CD03ABDAFCD8B063415F296C80D2FF71168E7CF69065EA70980048C2CE5F720C12361EB5FADF264AF0A02C5D5290BFB02681718BBF318F1131F6ECEB0152961F654C9C1F8D606DDE5A4AF8CE5D5BBBDCC1BEFFB797F130BB0567067DFCDEDB5B6ED718B3818ED7A0AFE3D55AC23A6D28A593300', domain='www.acadsoc.com.cn', path='/')
r = requests.get("https://www.acadsoc.com.cn/WebNew/user/TeachingMaterial/CurrentTextbook.aspx",cookies=jar)

soup = BeautifulSoup(r.text)
#print(soup.prettify())
BookName=soup.find("span",attrs={'class':"caption-subject bold uppercase"}).contents[0].strip()
mkdir(BookName)

def DownFile(filename,webpath):
    filename=filename.replace("/", " ")
    filename=filename.replace("\\", " ")
    filename=filename.replace("|", " ")
    filename=filename.replace("&", " and ")
    while(True):
        print('尝试读取下载:'+filename)
        try:
            r = requests.get("https://www.acadsoc.com.cn/"+webpath)
            with open(BookName+"/"+filename+".PDF", "w+b") as code:
                code.write(r.content)
            break
        except:
            print('下载解析异常:'+filename)
    print('下载完成:'+filename)

for item in soup.find("div",attrs={'class':"portlet-body"}).findAll("li",attrs={'class':'cor-sm-2 cor-md-2 cor-lg-2 danqianjc'}):
    title=item.find('li',attrs={'class':'cor-sm-10 cor-md-10 cor-lg-10 no-padding age tooltips'})['title'] +" "+ item.find('li',attrs={'class':'cor-sm-10 cor-md-10 cor-lg-10 ovestr tooltips'})['title']
    if item.find('a',attrs={'class':'text-success fa fa-book font-18'})==None:
        print(title + "没有下载地址!")
        continue
    href=item.find('a',attrs={'class':'text-success fa fa-book font-18'})['href']
    poolrequests = threadpool.makeRequests(DownFile, [([title,href],None)] )
    [Pool.putRequest(req) for req in poolrequests]

Pool.wait()
