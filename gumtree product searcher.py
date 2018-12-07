import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

##url = "https://www.gumtree.com.au/s-nintendo+ds+lite/k0?sort=price_asc"
##
##res = requests.get(url)#,headers=headers)
##print(res.status_code)
##if res.status_code == 200:
##    soup = BeautifulSoup(res.text, "lxml")
##    #div class="panel-body panel-body--flat-panel-shadow user-ad-collection__list-wrapper">
##    products = soup.findAll("a", attrs={"class":"user-ad-row link link--base-color-inherit link--hover-color-none link--no-underline"})
##    for product in products:
##        title = product.find("p", attrs={"class":"user-ad-row__title"}).text #<p class="user-ad-row__title">
##        print(title)

#size < 2147483648
#2^31 The number 2,147,483,647 (or hexadecimal 7FFF,FFFF16) is the maximum positive value for a 32-bit signed binary integer in computing
#max size = 2147483647

def collect_data(i,json_url,first=False):
    global products,pages
    print("Page:",i,json_url)
    response = requests.get(json_url)
    json_data = response.text
    if first:
        products = []
        pages = json.loads(json_data)['data']['pager']['lastPageNum']# pager lastPageNum
    print("Pages:","("+str(i)+"/"+str(pages)+")")
    resultlist = json.loads(json_data)['data']['results']['resultList']
    for result in resultlist:
        title = " ".join(result['title'].split()).replace(",","")
        price = result['priceText'].replace(",","").replace("$","")
        url = "https://www.gumtree.com.au/s-ad/"+str(result['id']).replace(",","")
        data = [price,title,url]
        if data not in products:
            #print("New")
            if dont_include not in data[1]: #if the don't include term isn't in the title
                products.append(data)
        else:
            pass
            #print("Old")

search_term = "hdd"
dont_include = "cable"

pages = 0
search_term_safe = urllib.parse.quote(search_term)
json_url = "https://www.gumtree.com.au/ws/search.json?keywords="+search_term_safe+"&pageNum=1&pageSize=2147483647&previousCategoryId=&radius=0&sortByName=price_asc"
collect_data(1,json_url,True)
if pages > 1:
    for i in range(2,pages+1):
        json_url = "https://www.gumtree.com.au/ws/search.json?keywords="+search_term_safe+"&pageNum="+str(i)+"&pageSize=2147483647&previousCategoryId=&radius=0&sortByName=price_asc"
        collect_data(i,json_url)
if pages == 13: #very likely to be missing a lot of entries due to 13 page limit (this is a partial workaround)
    extra_search_terms = ["","&sortByName=price_desc","&sortByName=rank"]
    for extra_term in extra_search_terms:
        for i in range(1,pages+1): #most recent,most expensive items,best match
            json_url = "https://www.gumtree.com.au/ws/search.json?keywords="+search_term_safe+"&pageNum="+str(i)+"&pageSize=2147483647&previousCategoryId=&radius=0"+extra_term
            collect_data(i,json_url)
print(len(products))
file_name = (search_term+" data.csv").replace(" ","_")
with open(file_name, "w", encoding="utf-8") as file:
    for product in products:
        file.write(",".join(product)+"\n")
print("Saved as '{}'".format(file_name))
