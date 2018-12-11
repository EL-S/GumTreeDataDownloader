import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
from tornado import ioloop, httpclient

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

def get_page_amount():
    global json_urls,search_term_safe
    json_url = "https://www.gumtree.com.au/ws/search.json?keywords="+search_term_safe+"&pageNum=1&pageSize=2147483647&previousCategoryId=&radius=0&sortByName=price_asc"
    response = requests.get(json_url)
    json_data = response.text
    collect_data(json_data,True)
    print("Pages to download:",pages)
    
def generate_json_urls():
    global json_urls,pages,search_term_safe
    if pages > 1:
        for i in range(2,pages+1):
            json_urls.append("https://www.gumtree.com.au/ws/search.json?keywords="+search_term_safe+"&pageNum="+str(i)+"&pageSize=2147483647&previousCategoryId=&radius=0&sortByName=price_asc")
    if pages == 13: #very likely to be missing a lot of entries due to 13 page limit (this is a partial workaround)
        extra_api_terms = ["","&sortByName=price_desc","&sortByName=rank"]
        for extra_api_term in extra_api_terms:
            for i in range(1,pages+1): #most recent,most expensive items,best match
                json_urls.append("https://www.gumtree.com.au/ws/search.json?keywords="+search_term_safe+"&pageNum="+str(i)+"&pageSize=2147483647&previousCategoryId=&radius=0"+extra_api_term)
def collect_data(json_data,first=False):
    global products,pages,dont_include
    if first:
        products = []
        pages = json.loads(json_data)['data']['pager']['lastPageNum']# pager lastPageNum
    resultlist = json.loads(json_data)['data']['results']['resultList']
    for result in resultlist:
        title = " ".join(result['title'].split()).replace(",","")
        price = result['priceText'].replace(",","").replace("$","")
        desc = " ".join(result['description'].split()).replace(",","")
        url = "https://www.gumtree.com.au/s-ad/"+str(result['id']).replace(",","")
        data = [price,title,url,desc]
        append_flag = False
        if data not in products:
            #print("New")
            for term in dont_include:
                if (term.lower() not in data[1].lower()) or (term == ""): #if the don't include term isn't in the title
                    append_flag = True
                else:
                    append_flag = False
                    break #found a term so stop the rest
        else:
            pass
        if append_flag == True:
            products.append(data)
        else:
            pass
            #print("Old or includes bad term(s)")

def save_csv():
    global search_term,products
    file_name = (search_term+" data.csv").replace(" ","_")
    with open(file_name, "w", encoding="utf-8") as file:
        for product in products:
            file.write(",".join(product)+"\n")
    print("Saved as '{}'".format(file_name))

def download_pages():
    global i,json_urls,total,http_client
    print(len(json_urls))
    i = 0
    http_client = httpclient.AsyncHTTPClient(force_instance=True,max_clients=threads)
    for json_url in json_urls:
        request = httpclient.HTTPRequest(json_url.strip(),method='GET',connect_timeout=4,request_timeout=4)
        http_client.fetch(request,handle_json_response)
        i += 1
    total = i
    print("Starting Download Of Pages...")
    ioloop.IOLoop.instance().start()

def handle_json_response(response):
    global http_client,i,products
    if response.code == 599: #retrying page
        #print(response.effective_url,"error")
        http_client.fetch(response.effective_url.strip(), handle_json_response, method='GET',connect_timeout=4,request_timeout=4)
    else:
        json_data = response.body.decode('utf-8') #automatic gzip decompress apparently
        try:
            collect_data(json_data)
            i -= 1
            print(str(round(((total-i)/total)*100,2))+"%")
        except Exception as e:
            http_client.fetch(response.effective_url.strip(), handle_json_response, method='GET',connect_timeout=4,request_timeout=4)
        if i == 0: #all pages loaded
            ioloop.IOLoop.instance().stop()
            print("Downloaded",len(products),"products")

search_term = input("Search Term: ")
dont_include = input("Don't Include Terms (comma seperated): ").split(",")

threads = 100 #configurable

pages = 0
json_urls = []
products = []

search_term_safe = urllib.parse.quote(search_term)

get_page_amount()
generate_json_urls()
download_pages()
save_csv()
