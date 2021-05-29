from bs4 import BeautifulSoup
import requests
import os
import concurrent.futures
import time
import re
from urllib.parse import unquote

# 存標題網址
data = []
# 存標題網址 的 後段
indexs = []
# 存照片網址
all_data = []

#爬 標題
def reptile_title(topic,search,page):
    page = str(page)
    
    #print(page)

    url = "https://www.ptt.cc/bbs/" + topic + "/search?page=" + page + "&q="+ search
    
    response = requests.get(url)

    # 檢查是否有頁面阻擋
    res_page = unquote(unquote(response.url))
    alert_page = "https://www.ptt.cc/ask/over18?from=/bbs/"+ topic +"/search?page="+ page + "&q=" + search

    #print(res_page)
    #print(alert_page)

    if res_page == alert_page :
        r = requests.Session()
        
        payload ={
            "from":"/bbs/" + topic + "/search?page=" + page + "&q="+ search,
            "yes":"yes"
        }
        r.post(alert_page,payload)
        rr = r.get(url)

    else:
        rr = response
        
    soup = BeautifulSoup(rr.text, "html.parser")

    a_tag = soup.find_all("div",class_="title")

    #print(a_tag)

    for i in range(len(a_tag)) :
        index = a_tag[i].find("a").get('href')
        indexs.append(index)
        data.append("https://www.ptt.cc/" + index)
        #print(url + "<>" + index)

    if page == "1" :
       a_tag = soup.find_all("a",class_="btn wide")
       all_page = a_tag[0].get('href')
       regex = re.compile(r'([0-9]{1,}[(&)])')
       match = regex.search(all_page)
       all_page = match.group(0).replace("&","")

       print("共 " + all_page + " 頁")

       return all_page

    #print("over")

#爬 照片
def reptile_photo(i) :
    url = data[i]
    response = requests.get(url)
    
    # 檢查是否有頁面阻擋
    res_page = unquote(unquote(response.url))
    alert_page = "https://www.ptt.cc/ask/over18?from="+ indexs[i]

    #print(res_page)
    #print(alert_page)

    if res_page == alert_page :
        r = requests.Session()
        
        payload ={
            "from":indexs[i],
            "yes":"yes"
        }   
        r.post(alert_page,payload)
        rr = r.get(url)

    else:
        rr = response

    soup = BeautifulSoup(rr.text, "html.parser")
    a_tag = soup.find_all("a",target="_blank")

    #print(str(i) + " start")

    time.sleep(0.1)
    for j in range(len(a_tag)) :
        if a_tag[j].text.find("imgur") != -1:
           if a_tag[j].text.find(".jpg") != -1:
              all_data.append(a_tag[j].text)
           else:
              all_data.append(a_tag[j].text + ".jpg")
        elif a_tag[j].text.find(".jpg") != -1:
           all_data.append(a_tag[j].text)
        elif a_tag[j].text.find(".png") != -1:
           all_data.append(a_tag[j].text)

    #print("over")

def write_txt():
    f = open("PTT_Photo.txt","w+")
    string = ""
    for i in range(len(all_data)):
        if all_data[i].find(".jpg") != -1:
           string = string + all_data[i] + "\n"
        else :
           string = string + all_data[i] + ".jpg\n"
    f.write(string)
    f.close()

def download_photo(url,i):
    img = requests.get(url)                                   # 下載圖片
    with open("images\\" + str(i+1) + ".jpg", "wb") as file:  # 開啟資料夾及命名圖片檔
         file.write(img.content)                              # 寫入圖片的二進位碼

if __name__ == "__main__":
    print("請鍵入主題:")
    topic = input()
    #topic = "car"
    print("請鍵入關鍵字")
    search = input()
    start_time = time.time()  # 

    page = 1
    all_page = int(reptile_title(topic,search,str(page)))

    if all_page >= 5 :
        print("目前僅搜尋前5頁")

        # 同時建立及啟用個執行緒
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        for i in range(2,6) :
            args = [topic,search,i]
            executor.submit(lambda p: reptile_title(*p),args)
        executor.shutdown()
    elif all_page > 1:
        print("正搜尋共 " + str(all_page) + " 頁")

        # 同時建立及啟用個執行緒
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=int(all_page))
        
        for i in range(2,int(all_page)) :
            args = [topic,search,i]
            executor.submit(lambda p: reptile_title(*p),args)
        executor.shutdown()

    length_title = len(data)
    
    print("共 " + str(length_title) + " 篇文章")

    print("搜尋圖片中...")
    #同時建立及啟用100個執行緒
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=100)

    for i in range(length_title) :
        executor.submit(reptile_photo,i)
    executor.shutdown()

    #reptile_photo(0)

    write_txt()

    if not os.path.exists("images"):
       os.mkdir("images")           # 建立資料夾

    # 同時建立及啟用150個執行緒
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=150)

    lenth_all = len(all_data)

    print("共 " + str(lenth_all) + " 張照片")
    print("下載圖片中...")

    for i in range(lenth_all):
        executor.submit(download_photo,all_data[i],i)

    executor.shutdown()

    end_time = time.time()
    print("共 " + str(round(end_time-start_time,2)) + " sec")
    time.sleep(0.1)
