# 시스템 모듈
import os
import io
import json
import sys
import re
import requests
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone


# Google Vision AI
from google.cloud import vision

# 플라스크 모듈
from flask import Flask, request, jsonify, render_template, send_file, make_response
from flask_session import Session
from flask_cors import CORS
import uuid

# 크롤링 모듈
from selenium import webdriver
from pyvirtualdisplay import Display
from bs4 import BeautifulSoup

# DB 모듈
import mysql.connector

# 이미지 모듈
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 



os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
client = vision.ImageAnnotatorClient()

# DB연결
def get_db_connection():
    return mysql.connector.connect()

# 상태정보
allCornerFlag = {
    "stateCorner1": {"flag": True},
    "stateCorner2": {"flag": True}
}

# 상태초기화
def reset_state():
    for corner in allCornerFlag:
        allCornerFlag[corner]["flag"] = True

@app.route('/')
def home():
    # record_visitor()
    return ''

# 코너상태 API
@app.route('/restaurant/corner/corners', methods=['GET'])
def responseAllFlag():
    return jsonify(allCornerFlag)

# 코너1 상태 True 변경 API
@app.route('/restaurant/corner/1/flagTrue', methods=['POST'])
def convertTrueCorner1():
    data = request.get_json()
    if not data:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    nowFlag = data.get('flag')
    if nowFlag is None:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    allCornerFlag["stateCorner1"]["flag"] = nowFlag
    return jsonify(allCornerFlag["stateCorner1"]), 200

# 코너1 상태 False 변경 API
@app.route('/restaurant/corner/1/flagFalse', methods=['POST'])
def convertFalseCorner1():
    data = request.get_json()
    if not data:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    nowFlag = data.get('flag')
    if nowFlag is None:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    allCornerFlag["stateCorner1"]["flag"] = nowFlag

    # 데이터베이스 연결 및 현재 시간 업데이트
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 현재 시간 가져오기
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record_date = datetime.now().strftime("%Y-%m-%d")


        # sold_out_time 업데이트 쿼리 실행
        update_query = "UPDATE Corner1 SET sold_out_time = %s WHERE date = %s"  
        cursor.execute(update_query, (current_time, record_date))
        
        # 변경 사항 커밋
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": "Failed to update sold_out_time"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify(allCornerFlag["stateCorner1"]), 200

# 코너2 상태 Trye 변경 API
@app.route('/restaurant/corner/2/flagTrue', methods=['POST'])
def convertTrueCorner2():
    data = request.get_json()
    if not data:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    nowFlag = data.get('flag')
    if nowFlag is None:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    allCornerFlag["stateCorner2"]["flag"] = nowFlag
    return jsonify(allCornerFlag["stateCorner2"]), 200

# 코너2 상태 False 변경 API
@app.route('/restaurant/corner/2/flagFalse', methods=['POST'])
def convertFalseCorner2():
    data = request.get_json()
    if not data:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    nowFlag = data.get('flag')
    if nowFlag is None:
        return jsonify({"오류": "잘못된 입력입니다."}), 400

    allCornerFlag["stateCorner2"]["flag"] = nowFlag

    # 데이터베이스 연결 및 현재 시간 업데이트
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 현재 시간 가져오기
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record_date = datetime.now().strftime("%Y-%m-%d")

        # sold_out_time 업데이트 쿼리 실행
        update_query = "UPDATE Corner2 SET sold_out_time = %s WHERE date = %s"  
        cursor.execute(update_query, (current_time, record_date))
        
        # 변경 사항 커밋
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": "Failed to update sold_out_time"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return jsonify(allCornerFlag["stateCorner2"]), 200

# 조식 좋아요 증가 함수
def increment_likes_breakfast():
    conn = None
    cursor = None
    try:
        # 현재 날짜 가져오기
        record_date = datetime.now().strftime("%Y-%m-%d")
        
        # 데이터베이스에 연결
        conn = get_db_connection()
        cursor = conn.cursor()

        # likes 값을 1 증가시키는 쿼리 작성
        query = "UPDATE Breakfast SET likes = likes + 1 WHERE date = %s"
        cursor.execute(query, (record_date,))

        # likes 값을 가져오는 쿼리 작성
        cursor.execute("SELECT likes FROM Breakfast WHERE date = %s", (record_date,))
        likes = cursor.fetchone()[0]

        # 변경 사항을 커밋
        conn.commit()
        
        print("Likes 값이 성공적으로 증가되었습니다.")
        return likes

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        # 커서와 연결을 닫음
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 조식 싫어요 증가 함수
def increment_dislikes_breakfast():
    conn = None
    cursor = None
    try:
        # 현재 날짜 가져오기
        record_date = datetime.now().strftime("%Y-%m-%d")
        
        # 데이터베이스에 연결
        conn = get_db_connection()
        cursor = conn.cursor()

        # dislikes 값을 1 증가시키는 쿼리 작성
        query = "UPDATE Breakfast SET dislikes = dislikes + 1 WHERE date = %s"
        cursor.execute(query, (record_date,))

        # dislikes 값을 가져오는 쿼리 작성
        cursor.execute("SELECT dislikes FROM Breakfast WHERE date = %s", (record_date,))
        dislikes = cursor.fetchone()[0]

        # 변경 사항을 커밋
        conn.commit()
        
        print("Dislikes 값이 성공적으로 증가되었습니다.")
        return dislikes

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        # 커서와 연결을 닫음
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너1 좋아요 증가 함수
def increment_likes():
    conn = None
    cursor = None
    try:
        # 현재 날짜 가져오기
        record_date = datetime.now().strftime("%Y-%m-%d")
        
        # 데이터베이스에 연결
        conn = get_db_connection()
        cursor = conn.cursor()

        # likes 값을 1 증가시키는 쿼리 작성
        query = "UPDATE Corner1 SET likes = likes + 1 WHERE date = %s"
        cursor.execute(query, (record_date,))

        # likes 값을 가져오는 쿼리 작성
        cursor.execute("SELECT likes FROM Corner1 WHERE date = %s", (record_date,))
        likes = cursor.fetchone()[0]

        # 변경 사항을 커밋
        conn.commit()
        
        print("Likes 값이 성공적으로 증가되었습니다.")
        return likes

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        # 커서와 연결을 닫음
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너1 싫어요 증가 함수
def increment_dislikes():
    conn = None
    cursor = None
    try:
        # 현재 날짜 가져오기
        record_date = datetime.now().strftime("%Y-%m-%d")
        
        # 데이터베이스에 연결
        conn = get_db_connection()
        cursor = conn.cursor()

        # dislikes 값을 1 증가시키는 쿼리 작성
        query = "UPDATE Corner1 SET dislikes = dislikes + 1 WHERE date = %s"
        cursor.execute(query, (record_date,))

        # dislikes 값을 가져오는 쿼리 작성
        cursor.execute("SELECT dislikes FROM Corner1 WHERE date = %s", (record_date,))
        dislikes = cursor.fetchone()[0]

        # 변경 사항을 커밋
        conn.commit()
        
        print("Dislikes 값이 성공적으로 증가되었습니다.")
        return dislikes

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        # 커서와 연결을 닫음
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너2 좋아요 증가 함수
def increment_likes2():
    conn = None
    cursor = None
    try:
        # 현재 날짜 가져오기
        record_date = datetime.now().strftime("%Y-%m-%d")
        
        # 데이터베이스에 연결
        conn = get_db_connection()
        cursor = conn.cursor()

        # likes 값을 1 증가시키는 쿼리 작성
        query = "UPDATE Corner2 SET likes = likes + 1 WHERE date = %s"
        cursor.execute(query, (record_date,))

        # likes 값을 가져오는 쿼리 작성
        cursor.execute("SELECT likes FROM Corner2 WHERE date = %s", (record_date,))
        likes = cursor.fetchone()[0]

        # 변경 사항을 커밋
        conn.commit()
        
        print("Likes 값이 성공적으로 증가되었습니다.")
        return likes

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        # 커서와 연결을 닫음
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너2 싫어요 증가 함수
def increment_dislikes2():
    conn = None
    cursor = None
    try:
        # 현재 날짜 가져오기
        record_date = datetime.now().strftime("%Y-%m-%d")
        
        # 데이터베이스에 연결
        conn = get_db_connection()
        cursor = conn.cursor()

        # dislikes 값을 1 증가시키는 쿼리 작성
        query = "UPDATE Corner2 SET dislikes = dislikes + 1 WHERE date = %s"
        cursor.execute(query, (record_date,))

        # dislikes 값을 가져오는 쿼리 작성
        cursor.execute("SELECT dislikes FROM Corner2 WHERE date = %s", (record_date,))
        dislikes = cursor.fetchone()[0]

        # 변경 사항을 커밋
        conn.commit()
        
        print("Dislikes 값이 성공적으로 증가되었습니다.")
        return dislikes

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        # 커서와 연결을 닫음
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 조식 싫어요 클릭 API
@app.route('/restaurant/corner/breakfast/dislikeClick', methods=['OPTIONS', 'POST'])
def dislike_click_breakfast():
    if request.method == 'OPTIONS':
        return "Dislike click handled", 200
    elif request.method == 'POST':
        dislikes = increment_dislikes()
        if dislikes is not None:
            return jsonify({"message": "Dislike click handled", "dislikes": dislikes}), 200
        else:
            return jsonify({"오류": "싫어요를 업데이트할 수 없습니다."}), 500

# 조식 좋아요 클릭 API
@app.route('/restaurant/corner/breakfast/likeClick', methods=['POST'])
def clickedLike_breakfast():
    likes = increment_likes()
    if likes is not None:
        return jsonify({"message": "Like click handled", "likes": likes}), 200
    else:
        return jsonify({"오류": "좋아요를 업데이트할 수 없습니다."}), 500

# 코너1 싫어요 클릭 API
@app.route('/restaurant/corner/1/dislikeClick', methods=['OPTIONS', 'POST'])
def dislike_click():
    if request.method == 'OPTIONS':
        return "Dislike click handled", 200
    elif request.method == 'POST':
        dislikes = increment_dislikes()
        if dislikes is not None:
            return jsonify({"message": "Dislike click handled", "dislikes": dislikes}), 200
        else:
            return jsonify({"오류": "싫어요를 업데이트할 수 없습니다."}), 500

# 코너1 좋아요 클릭 API
@app.route('/restaurant/corner/1/likeClick', methods=['POST'])
def clickedLike_corner1():
    likes = increment_likes()
    if likes is not None:
        return jsonify({"message": "Like click handled", "likes": likes}), 200
    else:
        return jsonify({"오류": "좋아요를 업데이트할 수 없습니다."}), 500

# 코너2 싫어요 클릭 API
@app.route('/restaurant/corner/2/dislikeClick', methods=['OPTIONS', 'POST'])
def dislike_click2():
    if request.method == 'OPTIONS':
        return "Dislike click handled", 200
    elif request.method == 'POST':
        dislikes = increment_dislikes2()
        if dislikes is not None:
            return jsonify({"message": "Dislike click handled", "dislikes": dislikes}), 200
        else:
            return jsonify({"오류": "싫어요를 업데이트할 수 없습니다."}), 500

# 코너2 좋아요 클릭 API
@app.route('/restaurant/corner/2/likeClick', methods=['POST'])
def clickedLike_corner2():
    likes = increment_likes2()
    if likes is not None:
        return jsonify({"message": "Like click handled", "likes": likes}), 200
    else:
        return jsonify({"오류": "좋아요를 업데이트할 수 없습니다."}), 500

# 조식 좋아요 값을 가져오는 API
@app.route('/restaurant/corner/breakfast/likes', methods=['GET'])
def get_likes_breakfast():
    conn = None
    cursor = None
    try:
        record_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT likes FROM Breakfast WHERE date = %s", (record_date,))
        likes = cursor.fetchone()[0]
        return jsonify({"likes": likes}), 200
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"오류": "좋아요를 불러올 수 없습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 조식 싫어요 값을 가져오는 API
@app.route('/restaurant/corner/breakfast/dislikes', methods=['GET'])
def get_dislikes_breakfast():
    conn = None
    cursor = None
    try:
        record_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dislikes FROM Breakfast WHERE date = %s", (record_date,))
        dislikes = cursor.fetchone()[0]
        return jsonify({"dislikes": dislikes}), 200
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"오류": "싫어요를 불러올 수 없습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너1 좋아요 값을 가져오는 API
@app.route('/restaurant/corner/1/likes', methods=['GET'])
def get_likes():
    conn = None
    cursor = None
    try:
        record_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT likes FROM Corner1 WHERE date = %s", (record_date,))
        likes = cursor.fetchone()[0]
        return jsonify({"likes": likes}), 200
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"오류": "좋아요를 불러올 수 없습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너1 싫어요 값을 가져오는 API
@app.route('/restaurant/corner/1/dislikes', methods=['GET'])
def get_dislikes():
    conn = None
    cursor = None
    try:
        record_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dislikes FROM Corner1 WHERE date = %s", (record_date,))
        dislikes = cursor.fetchone()[0]
        return jsonify({"dislikes": dislikes}), 200
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"오류": "싫어요를 불러올 수 없습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너2 좋아요 값을 가져오는 API
@app.route('/restaurant/corner/2/likes', methods=['GET'])
def get_likes2():
    conn = None
    cursor = None
    try:
        record_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT likes FROM Corner2 WHERE date = %s", (record_date,))
        likes = cursor.fetchone()[0]
        return jsonify({"likes": likes}), 200
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"오류": "좋아요를 불러올 수 없습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 코너2 싫어요 값을 가져오는 API
@app.route('/restaurant/corner/2/dislikes', methods=['GET'])
def get_dislikes2():
    conn = None
    cursor = None
    try:
        record_date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dislikes FROM Corner2 WHERE date = %s", (record_date,))
        dislikes = cursor.fetchone()[0]
        return jsonify({"dislikes": dislikes}), 200
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"오류": "싫어요를 불러올 수 없습니다."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 크롤링 함수 정의
def crawl_menu():
    try:
        sys.stdout.reconfigure(encoding='utf-8')

        # 학식 페이지 URL
        url = 'https://www.daelim.ac.kr/cms/FrCon/index.do?MENU_ID=1470'

        # Chrome 옵션 설정
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')  # 헤드리스 모드
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Selenium 웹 드라이버 초기화
        driver = webdriver.Chrome(options=chrome_options)

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

        # 요일 및 코너 정보 추출 (월요일~금요일까지만 추출)
        days = [day.get_text() for day in menu_table.select('thead th em')][:5]  # "월요일", "화요일", ...

        # 요일을 "월요일" -> "월"로 변환하는 함수
        def convert_day_to_short(day_str):
            return day_str[0]  # 첫 글자만 추출 (예: "월요일" -> "월")

        # 짧은 요일 형식 리스트
        short_days = [convert_day_to_short(day) for day in days]

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
                    menu_data[corner][day] = menu_items if menu_items else ["미운영"]
                else:
                    menu_data[corner][day] = ["미운영"]  # 요소가 없으면 "미운영" 추가

        # 요일에 따른 offset 계산을 위한 함수 (월~금까지만 처리)
        def calculate_target_date(short_day_of_week):
            today = datetime.now().weekday()  # 0: 월요일, 1: 화요일, ..., 6: 일요일
            if today > 4:  # 주말에는 금요일을 기준으로 계산
                today = 4
            target_day = ['월', '화', '수', '목', '금'].index(short_day_of_week)
            day_offset = target_day - today
            return (datetime.now() + timedelta(days=day_offset)).strftime('%Y-%m-%d')

        # 데이터베이스에 연결
        conn = get_db_connection()
        cursor = conn.cursor()

        # 날짜 및 데이터 삽입 처리
        for day, short_day in zip(days, short_days):  # 원본 요일과 짧은 요일을 함께 사용
            target_date = calculate_target_date(short_day)  # 요일에 맞는 실제 날짜 계산

            # Corner1 데이터 삽입
            if 'Corner1' in menu_data:
                menu_name = menu_data['Corner1'].get(day, ["미운영"])[0]
                try:
                    cursor.execute(
                        "INSERT INTO Corner1 (date, menu_name, likes, dislikes) VALUES (%s, %s, %s, %s)",
                        (target_date, menu_name, 0, 0)
                    )
                except mysql.connector.Error as err:
                    if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
                        print(f"중복된 항목 {target_date} - {menu_name} in Corner1")
                    else:
                        print(f"오류: {err}")

            # Corner2 데이터 삽입
            if 'Corner3' in menu_data:
                menu_name = menu_data['Corner3'].get(day, ["미운영"])[0]
                try:
                    cursor.execute(
                        "INSERT INTO Corner2 (date, menu_name, likes, dislikes) VALUES (%s, %s, %s, %s)",
                        (target_date, menu_name, 0, 0)
                    )
                except mysql.connector.Error as err:
                    if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
                        print(f"중복된 항목 {target_date} - {menu_name} in Corner3")
                    else:
                        print(f"오류: {err}")

            # 조식 데이터 삽입
            if '조식' in menu_data:
                menu_name = menu_data['조식'].get(day, ["미운영"])[0]
                try:
                    cursor.execute(
                        "INSERT INTO Breakfast (date, menu_name, likes, dislikes) VALUES (%s, %s, %s, %s)",
                        (target_date, menu_name, 0, 0)
                    )
                except mysql.connector.Error as err:
                    if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
                        print(f"중복된 항목 {target_date} - {menu_name} in Breakfast")
                    else:
                        print(f"오류: {err}")

        # DB 변경사항 커밋 및 닫기
        conn.commit()
        cursor.close()
        conn.close()

        global crawled_menu_data
        crawled_menu_data = menu_data

        print("크롤링된 데이터를 전역 변수에 저장했습니다.")
        return menu_data

    except Exception as e:
        print(f"크롤링 중 에러 발생: {e}")
        return None



# 음식 판별 함수
def detect_labels(image_blob):
    image = vision.Image(content=image_blob)

    # Face Detection 요청
    response = client.face_detection(image=image)
    faces = response.face_annotations

    # 얼굴이 감지되었는지 확인
    if faces:
        print("얼굴이 감지되었습니다. 해당 이미지를 제외합니다.")
        return False

    # 음식과 관련된 라벨 감지 요청
    response = client.label_detection(image=image)
    labels = response.label_annotations

    # 음식과 관련된 라벨 목록
    food_labels = ["Food", "Dish", "Cuisine", "Meal"]

    # 음식 라벨이 있는지 확인
    is_food = any(label.description in food_labels for label in labels)

    if response.error.message:
        raise Exception(f'{response.error.message}')

    # 음식 라벨이 있는 경우
    if is_food:
        print("음식입니다.")
        return True
    else:
        print("음식이 아닙니다.")
        return False

# 사진 업로드 API    
@app.route('/restaurant/corner/<int:corner_id>/upload', methods=['POST'])
def upload_image(corner_id):
    # Check if 'photo' is in the request files

    if 'photo' not in request.files:
        return jsonify({"에러:": "제공된 이미지가 없습니다."}), 400

    file = request.files['photo']

    # Ensure the file is an image
    if not file or not file.filename:
        return jsonify({"error": "파일이 선택되지 않았습니다."}), 400

    if not file.content_type.startswith('image/'):
        return jsonify({"error": "이미지 형식만 허용됩니다."}), 400

    cursor = None
    connection = None

    try:
        # Convert the file to binary
        photo_blob = file.read()

        # Use Google Vision AI to check if the image is a food photo
        is_food = detect_labels(photo_blob)

        if is_food:
            # Determine the table name based on corner_id
            if corner_id == 1:
                table_name = 'Corner1'
            elif corner_id == 2:
                table_name = 'Corner2'
            elif corner_id == 4:
                table_name = 'Breakfast'
            else:
                return jsonify({"error": "코너ID가 틀림."}), 400

            # Get today's date
            today_date = datetime.now().strftime('%Y-%m-%d')

            # Establish database connection
            connection = get_db_connection()
            cursor = connection.cursor()

            # Update query to set the photo for the current date
            query = f"""
            UPDATE {table_name}
            SET photo = %s
            WHERE date = %s;
            """
            
            cursor.execute(query, (photo_blob, today_date))
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({"error": "오늘 기록을 찾을 수 없습니다."}), 404

            return jsonify({"message": "성공적으로 파일이 업로드되었습니다."}), 200
        else:
            return jsonify({"error": "음식이미지가 아닙니다."}), 400

    except mysql.connector.Error as err:
        return jsonify({"error": f"데이터베이스 오류: {err}"}), 500
    except Exception as e:
        return jsonify({"error": f"오류 발생: {str(e)}"}), 500
    finally:
        # Close cursor and connection if they were created
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 조식 이미지 반환 API
@app.route('/restaurant/corner/breakfast/photo/<date>', methods=['GET'])
def get_image_corner_breakfast(date):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT photo FROM Breakfast WHERE date = %s"
        cursor.execute(query, (date,))
        result = cursor.fetchone()

        if not result or not result[0]:
            return jsonify({"error": "이미지를 찾을 수 없음"}), 404

        img_blob = result[0]

        img = Image.open(io.BytesIO(img_blob))
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=img.format)
        img_byte_arr.seek(0)        

        return send_file(img_byte_arr, mimetype=f'image/{img.format.lower()}')

    except Exception as e:
        return jsonify({"에러: ": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# 코너1 이미지 반환 API
@app.route('/restaurant/corner/1/photo/<date>', methods=['GET'])
def get_image_corner1(date):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT photo FROM Corner1 WHERE date = %s"
        cursor.execute(query, (date,))
        result = cursor.fetchone()

        if not result or not result[0]:
            return jsonify({"error": "이미지를 찾을 수 없음"}), 404

        img_blob = result[0]

        img = Image.open(io.BytesIO(img_blob))
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=img.format)
        img_byte_arr.seek(0)        

        return send_file(img_byte_arr, mimetype=f'image/{img.format.lower()}')

    except Exception as e:
        return jsonify({"에러: ": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# 코너2 이미지 반환 API
@app.route('/restaurant/corner/2/photo/<date>', methods=['GET'])
def get_image_corner2(date):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT photo FROM Corner2 WHERE date = %s"
        cursor.execute(query, (date,))
        result = cursor.fetchone()

        if not result or not result[0]:
            return jsonify({"error": "이미지를 찾을 수 없음"}), 404

        img_blob = result[0]
        img = Image.open(io.BytesIO(img_blob))

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=img.format)
        img_byte_arr.seek(0)

        return send_file(img_byte_arr, mimetype=f'image/{img.format.lower()}')

    except Exception as e:
        return jsonify({"에러: ": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# 메뉴 반환 API
@app.route('/restaurant/menu', methods=['GET'])
def get_menu():
    try:
        # 전역 변수에서 크롤링된 데이터를 가져와서 반환
        if crawled_menu_data:
            return jsonify(crawled_menu_data), 200
        else:
            return jsonify({"error": "메뉴가 존재하지 않습니다."}), 404
    except Exception as e:
        print(f"메뉴 데이터 반환 중 에러 발생: {e}")
        return jsonify({"error": "메뉴를 가져오지 못했습니다."}), 500

# 음식사진 삭제 API
@app.route('/restaurant/corner/<int:corner_id>/delete_photo', methods=['POST'])
def delete_photo(corner_id):
    # Validate corner_id
    if corner_id not in [1, 2, 'breakfast']:
        return jsonify({"error": "Invalid corner ID"}), 400

    # Get date from the request
    date = datetime.now().strftime('%Y-%m-%d')
    if not date:
        return jsonify({"error": "Date is required"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        if corner_id == 1:
            table_name = 'Corner1'
        elif corner_id == 2:
            table_name = 'Corner2'
        elif corner_id == 'breakfast':
            table_name = 'Breakfast'
        else:
            return jsonify({"error": "코너ID가 틀림."}), 400

        # Define the queries
        query = f"UPDATE {table_name} SET photo = NULL WHERE date = %s;"

        # Execute the query
        cursor.execute(query, (date,))
        connection.commit()

        # Check if any rows were affected
        if cursor.rowcount == 0:
            return jsonify({"message": "업데이트된 행 없음."}), 404

        return jsonify({"message": "이미지가 성공적으로 삭제됨."}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": f"데이터베이스 연결 오류!: {err}"}), 500

    finally:
        # Close cursor and connection if they were created
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 음식 판별 함수
# def detect_labels(blob_data):
    
#     client = vision.ImageAnnotatorClient()

#     image = vision.Image(content=blob_data)

#     # 라벨 감지 요청
#     response = client.label_detection(image=image)
#     labels = response.label_annotations

#     # print('감지된 라벨 :')
#     # for label in labels:
#     #     print(f"{label.description}")

#     # 음식 관련 라벨 존재 여부 확인
#     food_labels = ["Food", "Dish", "Cuisine", "Meal"]
#     is_food = any(label.description in food_labels for label in labels)

#     if is_food:
#         flag = True
#         #print("음식입니다.")
#     else:
#         flag = False
#         #print("음식이 아닙니다.")

#     if response.error.message:
#         raise Exception(f'{response.error.message}')
    
#     return flag

# 방문자를 기록하고 카운트 증가
# def record_visitor():
#     connection = get_db_connection()
#     cursor = connection.cursor()

#     try:
#         # 사용자의 IP 주소와 현재 날짜를 가져옴
#         ip_address = request.remote_addr
#         today_date = datetime.now().strftime('%Y-%m-%d')

#         # 쿠키를 통해 고유 방문자 인식
#         visitor_cookie_id = request.cookies.get('visitor_id')
#         if not visitor_cookie_id:
#             visitor_cookie_id = str(uuid.uuid4())  # 고유한 쿠키 ID 생성

#         # 방문자 정보가 이미 기록되었는지 확인
#         cursor.execute("SELECT * FROM VisitorInfo WHERE ip_address = %s AND visit_date = %s AND cookie_id = %s", 
#                        (ip_address, today_date, visitor_cookie_id))
#         result = cursor.fetchone()

#         if not result:
#             # 새로운 방문자라면 기록하고, 방문자 수 증가
#             cursor.execute("INSERT INTO VisitorInfo (ip_address, visit_date, cookie_id) VALUES (%s, %s, %s)", 
#                            (ip_address, today_date, visitor_cookie_id))

#             cursor.execute("SELECT count FROM VisitorCount WHERE date = %s", (today_date,))
#             result = cursor.fetchone()

#             if result:
#                 new_count = result[0] + 1
#                 cursor.execute("UPDATE VisitorCount SET count = %s WHERE date = %s", (new_count, today_date))
#             else:
#                 cursor.execute("INSERT INTO VisitorCount (date, count) VALUES (%s, %s)", (today_date, 1))
            
#             cursor.execute("SELECT total_count FROM TotalVisitorCount WHERE id = 1")
#             total_visitors = cursor.fetchone()

#             if total_visitors:
#                 new_total_count = total_visitors[0] + 1
#                 cursor.execute("UPDATE TotalVisitorCount SET total_count = %s WHERE id = 1", (new_total_count,))
#             else:
#                 cursor.execute("INSERT INTO TotalVisitorCount (id, total_count) VALUES (1, 1)")

#             connection.commit()

#         # 방문자를 인식한 쿠키를 설정하여 반환
#         response = make_response("Visitor recorded")  # 응답 메시지 설정
#         response.set_cookie('visitor_id', visitor_cookie_id, max_age=60*60*24*365)  # 쿠키를 1년간 유지
#         return response

#     except mysql.connector.Error as err:
#         return jsonify({"error": f"Database error: {err}"}), 500
#     finally:
#         cursor.close()
#         connection.close()

# @app.route('/restaurant/visitor_counts', methods=['GET'])
# def get_visitor_counts():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # 오늘의 날짜
        today_date = datetime.now().strftime('%Y-%m-%d')

        # 오늘의 방문자 수 가져오기
        cursor.execute("SELECT count FROM VisitorCount WHERE date = %s", (today_date,))
        today_visitors = cursor.fetchone()
        if today_visitors:
            today_visitors = today_visitors[0]
        else:
            today_visitors = 0

        # 총 누적 방문자 수 가져오기
        cursor.execute("SELECT total_count FROM TotalVisitorCount WHERE id = 1")
        total_visitors = cursor.fetchone()
        if total_visitors:
            total_visitors = total_visitors[0]
        else:
            total_visitors = 0

        return jsonify({
            "today_visitors": today_visitors,
            "total_visitors": total_visitors
        })

    except mysql.connector.Error as err:
        return jsonify({"error": f"데이터베이스 연결 오류! : {err}"}), 500
    finally:
        cursor.close()
        connection.close()

# 전역 변수 초기화
crawled_menu_data = None

# 스케줄러 설정
scheduler = BackgroundScheduler(daemon=True)
seoul_tz = timezone('Asia/Seoul')

scheduler.add_job(func=crawl_menu, trigger="cron", day_of_week='mon', hour=7, minute=0, timezone=seoul_tz)
scheduler.add_job(func=reset_state, trigger='cron', day_of_week='*', hour=6, minute=0, timezone=seoul_tz)

# 스케줄러 시작 후 작업 리스트를 출력해보기
scheduler.start()

if __name__ == '__main__':
    crawl_menu()
    app.run(debug=True, host="0.0.0.0", port=5002)
