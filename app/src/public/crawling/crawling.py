import sys
import json
import os
import re
import datetime
from selenium import webdriver
from bs4 import BeautifulSoup

# UTF-8로 인코딩
sys.stdout.reconfigure(encoding='utf-8')

os.makedirs('C:/vscode_workspace/extract_json', exist_ok=True)
file_path = "C:/vscode_workspace/extract_json"

# 학식 페이지 URL
url = 'https://www.daelim.ac.kr/cms/FrCon/index.do?MENU_ID=1470'

# Selenium 웹 드라이버 초기화
driver = webdriver.Chrome()

# 웹 페이지 열기
driver.get(url)

# 페이지가 완전히 로드될 때까지 기다리기
driver.implicitly_wait(5)

# 렌더링된 페이지의 HTML 가져오기
html = driver.page_source

# Selenium 브라우저 닫기
driver.quit()

# BeautifulSoup을 이용하여 HTML 파싱
soup = BeautifulSoup(html, 'html.parser')

# 메뉴 정보를 담을 딕셔너리 생성
menu_data = {}

# 메뉴 테이블 찾기
menu_table = soup.find('table', class_='lineTop_tb2')

# 요일 및 코너 정보 추출
days = [day.get_text() for day in menu_table.select('thead th em')]
corners = [corner.get_text() for corner in menu_table.select('tbody th')]

# 각 코너 및 요일에 대한 메뉴 추출
for i, corner in enumerate(corners):
    menu_data[corner] = {}
    for j, day in enumerate(days):
        # <td> 태그 내의 텍스트 가져오기
        td_selector = f'tbody tr:nth-child({i + 1}) td:nth-child({j + 2})'
        menu_items_element = menu_table.select_one(td_selector)
        
        # 요소가 존재하는 경우에만 처리
        if menu_items_element:
            menu_items = menu_items_element.get_text(separator='\n').strip()
            # 불필요한 공백 제거
            menu_items = [item.strip() for item in menu_items.split('\n') if item.strip()]
            menu_data[corner][day] = menu_items

json_data = json.dumps(menu_data, ensure_ascii=False, indent=4, sort_keys=True)

# 오늘 날짜 객체 생성
today = datetime.date.today()

# 날짜 문자열 생성
date_str = today.strftime("%m-%d")

# 파일 이름 설정
file_name = f"daelim_menu-{date_str}.json"

# 저장
with open(os.path.join(file_path, file_name), 'w', encoding='utf-8') as f:
    f.write(json_data)