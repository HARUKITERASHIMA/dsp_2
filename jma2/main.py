import requests
import json
import sqlite3
import flet as ft

# 地域情報JSONのパス
AREAS_JSON_PATH = "/Users/terashimaharuki/dsp_2/jma/areas.json"  # 実際のパスに変更してください

# 天気予報APIのURL
FORECAST_API_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"

# グローバル変数にregion_codesを定義
region_codes = {}

# データベースのファイルパス
DB_FILE = "weather.db"

def load_area_centers(file_path):
    """JSONファイルから地域情報を読み込む関数"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("centers", {}), data.get("offices", {})  # "centers" と "offices" を返す
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {file_path}")
        return None, None
    except json.JSONDecodeError:
        print(f"JSONの解析に失敗しました: {file_path}")
        return None, None

def fetch_weather_data(region_code):
    """指定された地域コードに基づいて天気予報情報を取得する関数"""
    try:
        url = FORECAST_API_URL.format(region_code=region_code)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # デバッグ: APIレスポンス全体を表示
        print(json.dumps(data, indent=2))  # ここでレスポンスの構造を確認する

        # 必要な情報を抽出
        if data:
            area_weather = data[0]['timeSeries'][0]['areas']  # 地域の天気情報全体
            area_forecasts = []

            # 地域ごとの天気情報を抽出
            for area in area_weather:
                area_forecast = {
                    "region": area["area"]["name"],
                    "details": []
                }

                time_defines = data[0]["timeSeries"][0]["timeDefines"]
                weathers = area["weathers"]
                winds = area["winds"]
                waves = area.get("waves", ["なし"] * len(weathers))

                max_length = len(time_defines)
                time_defines.extend(["N/A"] * (max_length - len(time_defines)))
                weathers.extend(["N/A"] * (max_length - len(weathers)))
                winds.extend(["N/A"] * (max_length - len(winds)))
                waves.extend(["なし"] * (max_length - len(waves)))

                # 各リストを最大長さに合わせる
                for time, weather, wind, wave in zip(time_defines, weathers, winds, waves):
                    area_forecast["details"].append({
                        "time": time,
                        "weather": weather,
                        "wind": wind,
                        "wave": wave,
                    })

                area_forecasts.append(area_forecast)

            return area_forecasts

        else:
            print("天気予報情報が取得できませんでした。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"APIへのリクエストに失敗しました: {e}")
        return None
    except json.JSONDecodeError:
        print("APIから取得したデータのJSON解析に失敗しました。")
        return None

def create_tables():
    """必要なテーブルを作成する"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefectures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region_id INTEGER,
            FOREIGN KEY (region_id) REFERENCES regions (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_name TEXT NOT NULL,
            prefecture_name TEXT NOT NULL,
            prefecture_id INTEGER,
            FOREIGN KEY (prefecture_id) REFERENCES prefectures (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_id INTEGER,
            date_time TEXT,
            weather TEXT,
            wind TEXT,
            wave TEXT,
            FOREIGN KEY (area_id) REFERENCES areas (id)
        )
        """)

        conn.commit()
    except sqlite3.Error as e:
        print(f"テーブル作成エラー: {e}")
    finally:
        conn.close()

def save_weather_data(area_forecasts):
    """天気情報をデータベースに保存する"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        for area_forecast in area_forecasts:
            # 地域情報を保存
            cursor.execute("INSERT INTO regions (name) VALUES (?)", (area_forecast["region"],))
            region_id = cursor.lastrowid

            for detail in area_forecast["details"]:
                # 天気情報を保存
                cursor.execute("""
                INSERT INTO weather (area_id, date_time, weather, wind, wave)
                VALUES (?, ?, ?, ?, ?)
                """, (region_id, detail["time"], detail["weather"], detail["wind"], detail["wave"]))

        conn.commit()
    except sqlite3.Error as e:
        print(f"データベースへの保存エラー: {e}")
    finally:
        conn.close()

def main(page: ft.Page):
    global region_codes  # グローバル変数として宣言

    page.title = "天気予報アプリ"
    page.scroll = "auto"  # スクロール可能に設定

    # ページの上部にタイトルを追加
    page.add(ft.Text("天気予報", theme_style="headline4", color="blue", text_align="center"))

    # 地域センター情報の読み込み
    centers, offices = load_area_centers(AREAS_JSON_PATH)

    if centers is None or offices is None:
        page.add(ft.Text("情報の読み込みに失敗しました", color="red"))
        return

    # 地域（地方）の選択肢を作成
    global region_codes
    region_codes = {}
    for center_code, center_info in centers.items():
        region_codes[center_code] = center_info["name"]

    # 地域選択のドロップダウン
    region_dropdown = ft.Dropdown(
        label="地域を選択", 
        options=[ft.dropdown.Option(region_name) for region_name in region_codes.values()],
        on_change=lambda e: update_offices(offices, e.control.value, page)  # 地域選択時に都道府県のリストを更新
    )
    page.add(region_dropdown)

    # 地方に関連する都道府県（市町村）選択肢を表示するためのエリア
    global office_dropdown
    office_dropdown = ft.Dropdown(
        label="都道府県を選択", 
        options=[],
        on_change=lambda e: update_weather(region_dropdown.value, e.control.value, page, region_codes, offices)  # 都道府県選択時に天気情報更新
    )
    page.add(office_dropdown)

    # 天気情報を表示するためのエリア
    global weather_area
    weather_area = ft.Column(
        alignment=ft.MainAxisAlignment.START,  # alignment を修正
        spacing=15,
        controls=[ft.Text("天気情報", theme_style="headline5", color="green")]
    )
    page.add(weather_area)

def update_offices(offices, region_name, page):
    """選択した地域に基づいて都道府県（市町村）を更新する関数"""
    # 地域コードを取得
    region_code = None
    for code, name in region_codes.items():
        if name == region_name:
            region_code = code
            break
    
    if region_code:
        office_options = []
        
        # 地域コードに基づいて都道府県のリストを取得
        for office_code, office_info in offices.items():
            if office_info.get("parent") == region_code:
                office_options.append(ft.dropdown.Option(office_info["name"]))
        
        office_dropdown.options = office_options
        page.update()

def update_weather(region_name, office_name, page, region_codes, offices):
    """選択した地域と都道府県に基づいて天気情報を表示する関数"""
    region_code = None
    office_code = None
    
    # 地域コードを取得
    for code, name in region_codes.items():
        if name == region_name:
            region_code = code
            break
    
    if region_code:
        # 都道府県コードを取得
        for code, office_info in offices.items():
            if office_info["name"] == office_name:
                office_code = code
                break

        if office_code:
            area_forecasts = fetch_weather_data(office_code)

            if area_forecasts:
                weather_area.controls = []  # 古い情報を消去
                for area_forecast in area_forecasts:
                    for detail in area_forecast["details"]:
                        weather_area.controls.append(ft.Text(f"{detail['time']} - {detail['weather']}"))
                page.update()
                save_weather_data(area_forecasts)

# アプリの開始
ft.app(target=main)
