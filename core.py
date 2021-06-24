#!/usr/bin/python3
# encoding: utf-8
"""
@author: m1n9yu3
@license: (C) Copyright 2021-2023, Node Supply Chain Manager Corporation Limited.
@file: test.py
@time: 2021/6/12 21:59
@desc:
"""
import os
import random
import HackRequests

import requests
from concurrent.futures import ThreadPoolExecutor
from lxml import etree
from PIL import Image
import string
import chardet


# headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
#            "Cookie":"__yjs_duid=1_7a7f2ea2da4844888712a3ceef86fa501620606471867; yjs_js_security_passport=d1cad68088e7610a97396ef7c2ce42b0cb547698_1624018399_js; ASPSESSIONIDCWBBDTAD=NFBDOCOBGJDMMIMHMOKPCIMP; Hm_lvt_f4ae163e87a012d4ab5106f993decb4c=1623505813,1624018312,1624018408; ASPSESSIONIDCWBCDRBD=CKGEOCOBNGCODKGCJGFAFLJN; Hm_lpvt_f4ae163e87a012d4ab5106f993decb4c=1624018664; Hm_lvt_99e7c52737fe82e187da07c6be46a37c=1624018413,1624018416,1624018511,1624018664; Hm_lpvt_99e7c52737fe82e187da07c6be46a37c=1624018664",
#            "Accept-Language":"zh-CN,zh;q=0.9",
#            "Pragma": "no-cache",
#            "Accept-Encoding":"gzip, deflate",
#            "Referer":"https://www.51test.net/",
#            "Sec-Fetch-Dest":"document",
#            "Sec-Fetch-User":"?1",
#            "Sec-Fetch-Mode":"navigate",
#            "Sec-Fetch-Site":"same-site",
#            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#            "Upgrade-Insecure-Requests":"1",
#            "sec-ch-ua-mobile":"?0",
#            "sec-ch-ua":'" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
#            "Cache-Control":"max-age=0"}
def random_str_png(num):
    return ''.join(random.sample(string.digits + string.ascii_letters, num)) + '.png'


def str2urlencode(s: str):
    res = s.encode('gb2312')
    res = str(res).replace("b'", "").upper().replace("'", "").replace("\\X", "%")
    return res


def combine2Pdf(files, pdfFilePath):
    try:
        folderPath = "tmp"

        pngFiles = []
        sources = []
        for file in files:
            png_content = requests.get(file)
            png_file_name = folderPath + '\\' + random_str_png(10)
            with open(file=png_file_name, mode="wb") as f:
                f.write(png_content.content)
            pngFiles.append(png_file_name)

        output = Image.open(pngFiles[0])
        output = output.convert("RGB")
        for file in pngFiles:
            pngFile = Image.open(file)
            if pngFile.mode != "RGB":
                pngFile = pngFile.convert("RGB")
            sources.append(pngFile)

        output.save(pdfFilePath, "pdf", save_all=True, append_images=sources)

        for file in pngFiles:
            os.remove(file)
    except Exception as e:
        print("发生了 ", e, pdfFilePath, files)


def get_shijuan(pdf_name: str, shijuan_url: str):
    step = 0
    try:
        step = 1
        response = requests.get(url=shijuan_url)
        step = 2
        image_list1 = etree.HTML(response.content.decode("gb2312")).xpath(
            "//div[@class='content-txt']/p/img//@data-src")
        if image_list1 != []:
            pdf_name = 'data\\data\\' + pdf_name + '.pdf'
            combine2Pdf(image_list1, pdf_name)
        else:
            file_url = etree.HTML(response.content.decode("gb2312")).xpath("//div[@class='content-txt']/p/a//@href")
            if not file_url:
                raise Exception("选取第二个标签时:%s" % shijuan_url)
            file_img_name = 'data\\data\\' + pdf_name.replace('\\', '') + '.doc'
            response = requests.get(url=file_url[0])
            with open(file=file_img_name, mode="wb") as f:
                f.write(response.content)
    except Exception as e:
        print("发生了%s, 错误, " % e, 'step:', step)


def parse_html(shijuan_url, shijuan_name, year='test'):
    print(shijuan_url)
    print(shijuan_name)
    if not os.path.exists('data\\%s' % year):
        os.mkdir('data\\%s' % year)
    with ThreadPoolExecutor(max_workers=5) as T:
        Threads = [T.submit(get_shijuan, shijuan_name[i], shijuan_url[i]) for i in range(len(shijuan_url))]
        [i.done() for i in Threads]


def search(subject: str, area: str, page=-1):
    # proxy = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
               "Referer": "https://www.51test.net/"}
    pre_page_data = None

    if page == -1:
        page = 1000

    for i in range(page):
        try:
            url = 'https://list.51test.net/w/?nclassid=144&search_key={}&search_key2={}&page={}'.format(
                str2urlencode(subject), str2urlencode(area), str(i))
            response = requests.get(url=url, headers=headers)
            if response.url == 'https://www.51test.net/':
                return
            ett = etree.HTML(response.content.decode('gb2312'))
        except:
            break

        shijuan_name = ett.xpath("//div[@class='news-list-left-content']/ul/li/a//text()")
        shijuan_url = ett.xpath("//div[@class='news-list-left-content']/ul/li/a//@href")
        if pre_page_data == shijuan_name or shijuan_name == []:
            break
        pre_page_data = shijuan_name

        parse_html(shijuan_url, shijuan_name)


def search_data():
    subject = input("请输入学科:")
    area = input("请输入地区:")
    search(subject, area)


if __name__ == '__main__':
    search_data()
