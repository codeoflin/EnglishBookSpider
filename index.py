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
r = requests.get("https://dict.eudic.net/ting/article?id=a6ffabd7-d344-4b33-a48b-9d3661ee818c")
#print(r.status_code)

soup = BeautifulSoup(r.text)
#soup = BeautifulSoup(open('index.html'))

#print(soup.prettify())
Menu2=[]
for menu1item in soup.findAll('dl',attrs={'class':'cl_item'}):
    if menu1item.dt.text in ['用户上传','综合听力','VIP专属','娱乐学习']:
        continue
    if not menu1item.dt.text in ['美式英语']:#测试
        continue
    for menu2item in menu1item.findAll('a'):
        menu2item['href']='https://dict.eudic.net'+menu2item['href']
        Menu2.append({'menu1name':menu1item.dt.text,'menu2name':menu2item['alt'],'url':menu2item['href']})
        # print(menu2item['alt'] +"  "+ menu2item['href'])

# 根据2级菜单的链接,请求页面,并从中获取3级菜单
Menu3=[]
def ParseMenu2(menu2item):
    menu3=None
    while(True):
        print('尝试读取解析:'+menu2item['menu2name'])
        try:
            menu3=BeautifulSoup(requests.get(menu2item['url'], timeout=10).text)
        except:
            print('读取解析异常:'+menu2item['menu2name'])
            continue
        if menu3.find('div',attrs={'class':'error-message'})==None:
            break
        print('读取解析失败:'+menu2item['menu2name'])
    print('读取解析完成:'+menu2item['menu2name'])
    if not menu2item['menu2name'] in ['新概念美语']:#测试
        return
    for menu3item in menu3.find('div',attrs={'class':'contents frap'}).findAll('dl'):
        Menu3.append({'menu1name':menu2item['menu1name'],'menu2name':menu2item['menu2name'],'menu3name':menu3item['title'],'id':menu3item['id']})

for item in Menu2:
    poolrequests = threadpool.makeRequests(ParseMenu2, (item,)) 
    [Pool.putRequest(req) for req in poolrequests]

Pool.wait()

# 根据3级菜单的id获取4级菜单(最后一级)
Menu4=[]
def ParseMenu3(menu3item):
    data=None
    while(True):
        print('尝试读取解析:'+menu3item['menu3name'])
        try:
            data=BeautifulSoup(requests.get('https://dict.eudic.net/ting/article?id='+menu3item['id'], timeout=10).text)
        except:
            print('读取解析异常:'+menu3item['menu3name'])
            continue
        if data.find('div',attrs={'class':'contents frap'})!=None:
            break
        print('读取解析失败:'+menu3item['menu3name'])
    print('读取解析完成:'+menu3item['menu3name'])
    for menu4item in data.find('div',attrs={'class':'contents frap'}).findAll('dl'):
        if menu4item.a['href']=='javascript:void(0)':
            print('需要客户端:'+menu4item['title'])
            continue
        Menu4.append({'menu1name':menu3item['menu1name'],'menu2name':menu3item['menu2name'],'menu3name':menu3item['menu3name'],'menu4name':menu4item['title'],'url':'https://dict.eudic.net'+menu4item.a['href']})

for item in Menu3:
    poolrequests = threadpool.makeRequests(ParseMenu3, (item,))
    [Pool.putRequest(req) for req in poolrequests]

Pool.wait()


# 根据4级菜单的url下载内容

def ParseMenu4(menu4item):
    allpath='数据/'+strB2Q(menu4item['menu1name'])
    mkdir(allpath)
    allpath=allpath+'/'+strB2Q(menu4item['menu2name'])
    mkdir(allpath)
    allpath=allpath+'/'+strB2Q(menu4item['menu3name'])
    mkdir(allpath)
    allpath=allpath+'/'+strB2Q(menu4item['menu4name'])
    mkdir(allpath)

    while(True):
        print('尝试读取解析:'+menu4item['menu4name'])
        try:
            text=requests.get(menu4item['url'], timeout=5).text
            data=BeautifulSoup(text)
            datatype=CheckType(data)
            if datatype==0:
                print('不认识的数据类型:'+menu4item['url']) 
                break
            if datatype==1:
                mp3url=text[text.find('initPlayPage')+14:]
                mp3url=mp3url[:mp3url.find('"')]
                r = requests.get(mp3url)
                with open(allpath+"/Audio.MP3", "w+b") as code:
                    code.write(r.content)
                article=data.find('div',attrs={'id':'article'})
                paragraphs=article.findAll('p',attrs={'class':'paragraph'})
                
                translate=json.loads(Type1TranslateSearcher.findall(text)[0])
                paragraphdata=[]
                for paragraph in paragraphs:
                    paragraphdata.append({'starttime':paragraph.span.attrs['data-starttime'],'endtime':paragraph.span.attrs['data-endtime'],'english':paragraph.span.text})
                jsontext=json.dumps({'Type':1,'Text':paragraphdata,'Translate':translate,'Menu1Name':menu4item['menu1name'],'Menu2Name':menu4item['menu2name'],'Menu3Name':menu4item['menu3name'],'Menu4Name':menu4item['menu4name']},ensure_ascii=False)
                with open(allpath+"/information.json", 'w+',encoding='utf-8') as f:    #写入numpy.ndarray数据
                    f.write(jsontext)

        except:
            print('读取解析异常:'+menu4item['menu4name'])
            continue

    print('读取解析完成:'+menu4item['menu4name']) 

mkdir('数据')
for item in Menu4:
    poolrequests = threadpool.makeRequests(ParseMenu4, (item,))
    [Pool.putRequest(req) for req in poolrequests]

Pool.wait()
