from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
import time

keywords = [
    '대통령',
    '바이든',

    ]

for cnt in range(100, 106):
    naver_url = "https://news.naver.com/section/"
    naver_inner_url = "https://news.naver.com"  
    
    naver_tabs = f"{naver_url}{cnt}"        
    html = urlopen(naver_tabs)

    bsObject = bs(html, 'html.parser', from_encoding='utf-8')       
    tab_name = bsObject.select("h2.ct_snb_h2 > a")
    li_link = bsObject.select("ul.ct_snb_nav > li > a")

    tab_name = tab_name[0].get_text()


    for line in li_link:
        time.sleep(0.2)
        
        msg = f"'{tab_name}'탭의 '{line.getText()}' 뉴스를 확인합니다"
        print(msg)

        # with open("text.txt", "a", encoding="UTF-8") as f:
        #      f.write(msg+"\n")

        tab_inner_link = line['href']

        inner_url = naver_inner_url + tab_inner_link
        
        inner_html = urlopen(inner_url)
        innerObject = bs(inner_html, 'html.parser', from_encoding='utf-8')
        recent_news = innerObject.select('#newsct > div.section_latest > div > div.section_latest_article._CONTENT_LIST._PERSIST_META > div:nth-child(1) > ul')

        links = [{'href': a['href'], 'title': a.get_text(strip=True)} 
            for div in recent_news 
            for a in div.find_all('a') if a.get_text(strip=True)]
        
        keyword_match_news = [link for link in links if any(keyword in link['title'] for keyword in keywords)]

        for line in keyword_match_news:
            print(line['title'])
        
        
        # for line in links:
        #     # print(line)
        #     with open("text.txt", "a", encoding="UTF-8") as f:
        #         f.write(line['href'])
        #         f.write(line['title'])
        #         f.write("\n")

    break