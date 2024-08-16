import flet as ft
from flet import cupertino_colors as cuper
import dbInit
import sqlite3, re, os, threading, time
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
import pyperclip

DB_NAME = "news.db"
DB_PATH = "RESULT"
DB_FULL_PATH = "RESULT/news.db"

def fetch_keywords(database_path):
    """데이터베이스에서 키워드를 로드합니다."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT keyword FROM keyword")
    keywords = [item[0] for item in cursor.fetchall()]
    conn.close()
    return keywords

def Remove_Special_Character(news_title):
    return re.sub(r'[-‧=+,#/\?:^.@*\"※~ㆍ!』‘|\(\)\[\]`\'…》\”\“\’·]', ' ', news_title)

def save_news_to_db(keyword_match_news):
    # 뉴스 데이터를 데이터베이스에 저장
    conn = sqlite3.connect(DB_FULL_PATH)
    cursor = conn.cursor()
    for news in keyword_match_news:
        cursor.execute('''
            INSERT OR IGNORE INTO news (title, url, checked) VALUES (?, ?, ?);
        ''', (news['title'], news['href'], '0'))
    conn.commit()
    conn.close()

def get_unchecked_news():
    conn = sqlite3.connect(DB_FULL_PATH)
    cursor = conn.cursor()

    # checked가 0인 뉴스 가져오기
    cursor.execute("SELECT title, url FROM news WHERE checked = 0")
    news_list = [{"title": row[0], "url": row[1]} for row in cursor.fetchall()]

    # 가져온 뉴스는 checked를 1로 업데이트
    cursor.executemany("UPDATE news SET checked = 1 WHERE url = ?", [(news["url"],) for news in news_list])

    conn.commit()
    conn.close()

    return news_list

class NewsCollectorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.theme_mode = ft.ThemeMode.LIGHT  # 초기 테마 모드를 설정합니다.
        # self.page.bgcolor = ft.colors.WHITE24
        self.page.window.width = 900
        self.page.window.height = 730
        
        self.crawling_thread = None
        self.crawling_active = threading.Event()
        
        self.alarm_icon = ft.Icon(ft.icons.NOTIFICATIONS_ACTIVE, color=ft.colors.RED, visible=False)  # 알람 아이콘 생성

        self.create_appbar()
        self.create_status_cards()
        self.create_list_views()
        self.create_buttons()
        self.create_text_fields()
        self.create_containers()
        self.build_layout()

        self.db_init()
        self.keyword_init()

        self.page.update()

    def create_appbar(self):
        self.page.appbar = ft.AppBar(
            leading=ft.Icon(ft.icons.NEWSPAPER),
            leading_width=40,
            title=ft.Text("뉴스 수집기"),
            center_title=False,
            bgcolor=ft.colors.BROWN_300,
            actions=[
                ft.IconButton(ft.icons.WB_SUNNY_OUTLINED, on_click=self.check_thememode_clicked),
            ],
        )

    def show_alarm(self):
        # 알람 아이콘을 표시하고 3초 후에 사라지게 설정
        self.alarm_icon.visible = True
        self.page.update()
        threading.Timer(3.0, self.hide_alarm).start()

    def hide_alarm(self):
        # 알람 아이콘을 숨김
        self.alarm_icon.visible = False
        self.page.update()

    def db_init(self):
        dbInit.db_init()

    def keyword_init(self):
        keywords = dbInit.keyword_init()

        self.keyword_list.controls.clear()
        
        for keyword in keywords:
            self.add_keyword_to_list(keyword)

        self.page.update()

    def on_submit_save_keyword(self, e):
        keyword = e.control.value
        keywords = dbInit.keyword_save(keyword)

        # 필요시 keyword를 다른 곳에 저장하거나 추가 작업 수행 가능
        e.control.value = ""  # 입력 필드 초기화

        if keywords[:2] == "이미":
            self.message_text.value = "키워드가 이미 존재합니다."
        else:
            self.keyword_list.controls.clear()
            for keyword in keywords:
                self.add_keyword_to_list(keyword)
            self.message_text.value = "키워드 추가되었습니다."
        
        e.control.focus()
        self.page.update()

    def on_submit_delete_keyword(self, e):
        keyword = e.control.value
        keywords = dbInit.keyword_delete(keyword)
        e.control.value = ""  # 입력 필드 초기화

        self.keyword_list.controls.clear()
        
        for keyword in keywords:
            self.add_keyword_to_list(keyword)

        self.message_text.value = "키워드 삭제되었습니다."
        e.control.focus()
        self.page.update()

    def delete_keyword(self, e, clicked_keyword):
        keywords = dbInit.keyword_delete(clicked_keyword)

        self.keyword_list.controls.clear()

        for keyword in keywords:
            self.add_keyword_to_list(keyword)

        self.message_text.value = "키워드 삭제되었습니다."
        self.page.update()

    def add_keyword_to_list(self, keyword):
        self.keyword_list.controls.append(
            ft.TextButton(
                text=keyword, 
                on_click=lambda e: self.keyword_clicked(e, keyword),
                
            )
        )

    def keyword_clicked(self, e, keyword):
        self.delete_keyword(e, keyword)

    ###################
    # 상단 Cards 생성 #
    ###################
    def create_status_cards(self):
        self.news_status_card = ft.Card(
            content=ft.Container(
                content=ft.Text(
                    "뉴스 현황",
                    style=ft.TextStyle(
                        size=15,
                        weight=ft.FontWeight.BOLD
                        )
                    ),
                padding=10
            ),
            elevation=2
        )
        self.keyword_status_card = ft.Card(
            content=ft.Container(
                content=ft.Text(
                    "키워드 현황",
                    style=ft.TextStyle(
                        size=15,
                        weight=ft.FontWeight.BOLD
                        )
                    ),
                padding=10
            ),
            elevation=2
        )
        self.state_status_card = ft.Card(
            content=ft.Container(
                content=ft.Text(
                    "진행 현황",
                    style=ft.TextStyle(
                        size=15,
                        weight=ft.FontWeight.BOLD
                        )
                    ),
                padding=10
            ),
            elevation=2,
            
        )

    #############
    # 뷰잉 전용 #
    #############
    def create_list_views(self):
        self.news_list = ft.ListView(
                expand=1, spacing=10, padding=10, auto_scroll=False,
            )
        self.news_container = ft.Container(
            content=self.news_list,
            padding=ft.padding.all(10),
            border=ft.border.all(2, ft.colors.BLACK),
            margin=ft.margin.only(left=5, top=5),
            expand=True,
        )

        self.keyword_list = ft.ListView(
            expand=1, spacing=10, padding=10, auto_scroll=True
        )
        self.keyword_container = ft.Container(
            content=self.keyword_list,
            width=400,
            height=220,
            border=ft.border.all(2, ft.colors.BLACK),
            # padding=ft.padding.all(10),
            margin=ft.margin.only(left=5, top=5),
            expand=True,
        )

        self.state_list = ft.ListView(
                expand=1, spacing=10, padding=10, auto_scroll=True,
            )
        self.state_container = ft.Container(
            content=self.state_list,
            padding=ft.padding.all(10),
            border=ft.border.all(2, ft.colors.BLACK),
            margin=ft.margin.only(left=5, top=5),
            expand=True,
        )

    #################
    # 입력 필드 전용 #
    #################
    def create_text_fields(self):
        self.keyword_input = ft.TextField(
            label="키워드 입력, 입력 후 엔터",
            width=280, 
            height=40, 
            on_submit = self.on_submit_save_keyword,
        )

        self.keyword_input_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.keyword_input,
                            # self.keyword_delete
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    # self.message_text  # 메시지 텍스트 추가
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(top=5)  # 상단 패딩 추가
        )

    ############
    # 버튼 생성 #
    ############
    def create_buttons(self):
        self.news_start_btn = ft.ElevatedButton(
            width=170,
            height=40,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(value="뉴스 수집 시작", size=14)
                    ]
                ),
                padding=ft.padding.all(10),
                on_click=self.start_crawling,
            )
        )
        self.news_start_container = ft.Container(
            content=self.news_start_btn,
            padding=ft.padding.only(left=10, top=10),
        )

        self.news_stop_btn = ft.ElevatedButton(
            width=170,
            height=40,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(value="뉴스 수집 중지", size=14)
                    ]
                ),
                padding=ft.padding.all(10),
                on_click=self.stop_crawling,
            )
        )
        self.news_stop_container = ft.Container(
            content=self.news_stop_btn,
            padding=ft.padding.only(left=10, top=10),
        )

    ##################
    # 뉴스 파싱 관련 #
    #################
    def start_crawling(self, e):
        if self.crawling_thread is None:
            self.crawling_active.set()
            self.crawling_thread = threading.Thread(target=self.crawl_news_loop)
            self.crawling_thread.start()
        self.message_text.value = "뉴스 수집을 시작합니다."
        self.page.update()

    def stop_crawling(self, e):
        if self.crawling_thread is not None:
            self.crawling_active.clear()
            self.crawling_thread.join()
            self.crawling_thread = None
        self.message_text.value = "뉴스 수집이 중지되었습니다."
        self.page.update()

    def crawl_news_loop(self):
        while self.crawling_active.is_set():
            self.crawl_naver_news()

    def add_state_message(self, msg):
        self.state_list.controls.append(ft.Text(msg))
        
        self.page.update()

    def crawl_naver_news(self):
        self.state_list.controls.clear()

        for cnt in range(100, 106):
            if not self.crawling_active.is_set():
                break
            # 네이버 뉴스

            keywords = fetch_keywords(DB_FULL_PATH)  # 키워드 로드

            naver_url = "https://news.naver.com/section/"
            naver_inner_url = "https://news.naver.com" 

            naver_tabs = f"{naver_url}{cnt}"
            html = urlopen(naver_tabs)

            bsObject = bs(html, 'html.parser', from_encoding='utf-8')
            tab_name = bsObject.select("h2.ct_snb_h2 > a")
            li_link = bsObject.select("ul.ct_snb_nav > li > a")

            tab_name = tab_name[0].get_text()

            for line in li_link:
                if not self.crawling_active.is_set():
                    break
                time.sleep(0.2)

                msg = f"'{tab_name}'탭의 '{line.getText()}' 뉴스를 확인합니다"

                self.add_state_message(msg)
                tab_inner_link = line['href']

                inner_url = naver_inner_url + tab_inner_link

                inner_html = urlopen(inner_url)
                innerObject = bs(inner_html, 'html.parser', from_encoding='utf-8')

                recent_news = innerObject.select('#newsct > div.section_latest > div > div.section_latest_article._CONTENT_LIST._PERSIST_META > div:nth-child(1) > ul')     

                links = [{'href': a['href'], 'title': a.get_text(strip=True)} 
                    for div in recent_news 
                    for a in div.find_all('a') if a.get_text(strip=True)]       
            
                keywords_match_news = [link for link in links if any(keyword in link['title'] for keyword in keywords)]

                if keywords_match_news:
                    save_news_to_db(keywords_match_news)

                unchecked_news = get_unchecked_news()

                if unchecked_news:
                    for news in unchecked_news:
                        formatted_news = f"{news['title']}\n{news['url']}"
                        self.add_news_to_list(formatted_news)

    def news_clicked(self, news):
        # 클립보드에 텍스트 복사
        pyperclip.copy(news)
        self.message_text.value = "클립보드에 복사되었습니다."
        self.page.update()

    def add_news_to_list(self, news):
        # 현재 리스트에 포함된 항목의 수를 기반으로 색상을 선택
        row_index = len(self.news_list.controls)

        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            # 라이트 모드에서의 배경색 설정
            bgcolor_even = ft.colors.GREY_800
            bgcolor_odd = ft.colors.GREY_900
            text_color = ft.colors.WHITE
        else:
            # 다크 모드에서의 배경색 설정
            bgcolor_even = ft.colors.GREY_800
            bgcolor_odd = ft.colors.GREY_900
            text_color = ft.colors.WHITE

        # 줄마다 다른 배경색 적용
        bgcolor = bgcolor_even if row_index % 2 == 0 else bgcolor_odd

        self.news_list.controls.insert(
            0,
            ft.Container(
                content=ft.TextButton(
                    content=ft.Container(
                        content=ft.Text(news, color=text_color),
                        padding=ft.padding.all(10),
                        alignment=ft.alignment.center_left,
                    ),
                    on_click=lambda e: self.news_clicked(news),
                ),
                bgcolor=bgcolor,
                padding=ft.padding.all(5),
            )
        )
        self.page.update()
        self.show_alarm()

    def create_containers(self):
        # 메시지를 표시할 Text 컨트롤 생성
        self.message_text = ft.Text(value="", color=ft.colors.RED)

    def build_layout(self):
        self.page.add(
            ft.Row(
                controls=[
                    self.news_status_card,
                    self.news_start_btn,
                    self.news_stop_btn,
                    self.message_text,
                    self.alarm_icon,
                ],
            ),
            self.news_container,

            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    self.keyword_status_card,
                                    self.keyword_input_container,
                                ]
                            ),
                            self.keyword_container,
                        ],
                    ),
                    ft.Column(
                        controls=[
                            self.state_status_card,
                            self.state_container,
                        ],
                        expand=True,
                    )
                ],
                expand=True,
            )

        )

    # 테마 밝기 조절
    def check_thememode_clicked(self, e):
        # 현재 테마 모드를 확인하고 반대 모드로 설정합니다.
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            # 다크 모드일 때 테두리 흰색으로 변경
            self.news_container.border = ft.border.all(2, ft.colors.WHITE)
            self.state_container.border = ft.border.all(2, ft.colors.WHITE)
            self.keyword_container.border = ft.border.all(2, ft.colors.WHITE)
            self.keyword_input.border_color=ft.colors.WHITE
            self.page.bgcolor = ft.colors.BLACK  # 페이지 배경색을 변경합니다.
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            # 라이트 모드일 때 테두리 검정색으로 변경
            self.news_container.border = ft.border.all(2, ft.colors.BLACK)
            self.state_container.border = ft.border.all(2, ft.colors.BLACK)
            self.keyword_container.border = ft.border.all(2, ft.colors.BLACK)
            self.keyword_input.border_color=ft.colors.BLACK
            self.page.bgcolor = ft.colors.ON_SECONDARY  # 페이지 배경색을 변경합니다.

        self.page.update()

def main(page: ft.Page):
    NewsCollectorApp(page)

ft.app(target=main)
