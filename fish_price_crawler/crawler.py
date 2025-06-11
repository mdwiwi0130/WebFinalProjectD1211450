import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import traceback
import sys
import time

# 設置標準輸出編碼為 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 載入環境變數
load_dotenv()

def get_db_connection():
    """建立資料庫連線"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'prices.db')
        print(f"資料庫路徑: {db_path}")
        return sqlite3.connect(db_path)
    except Exception as e:
        print(f"資料庫連接錯誤: {str(e)}")
        raise

def create_table():
    """建立資料表"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS tilapia_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            product_name VARCHAR(50) NOT NULL,
            avg_price DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(sql)
        conn.commit()
        print("資料表創建/檢查完成")
    finally:
        cursor.close()
        conn.close()

def check_date_exists(conn, date, fish_name):
    """檢查日期和魚種是否已存在"""
    cursor = conn.cursor()
    try:
        sql = "SELECT COUNT(*) FROM tilapia_prices WHERE date = ? AND product_name = ?"
        cursor.execute(sql, (date, fish_name))
        count = cursor.fetchone()[0]
        print(f"檢查日期 {date} 和魚種 {fish_name} 是否存在: {'是' if count > 0 else '否'}")
        return count > 0
    finally:
        cursor.close()

def make_request(url, max_retries=3):
    """發送請求並處理重試邏輯"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            print(f"嘗試請求 {url} (第 {attempt + 1} 次)")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print("請求成功")
            return response
        except requests.exceptions.Timeout:
            print(f"請求超時 (第 {attempt + 1} 次)")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒後重試
                continue
            raise
        except requests.exceptions.RequestException as e:
            print(f"請求錯誤: {str(e)} (第 {attempt + 1} 次)")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise

def crawl_fish_price(fish_name="吳郭魚", ask_confirmation=True, return_data_only=False):
    """爬取魚價資料"""
    url = "https://efish.fa.gov.tw/efish/statistics/simplechart.htm"
    status = "未完成"
    details = []
    
    try:
        print(f"開始訪問URL: {url}")
        details.append("開始訪問漁業署網站...")
        # 發送請求
        response = make_request(url)
        print("成功獲取網頁內容")
        details.append("成功獲取網頁內容")
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        print("HTML解析完成")
        details.append("HTML解析完成")
        
        # 找到所有價格表格
        tables = soup.find_all('table')
        print(f"找到 {len(tables)} 個表格")
        target_table = None
        table_type = ""
        
        # 搜索所有表格，找到包含目標魚種的表格
        for i, table in enumerate(tables):
            print(f"檢查表格 {i+1}")
            table_text = table.get_text()
            if fish_name in table_text:
                target_table = table
                # 判斷表格類型
                if '養殖類' in table_text:
                    table_type = "養殖類"
                elif '海水魚類' in table_text:
                    table_type = "海水魚類"
                elif '淡水魚類' in table_text:
                    table_type = "淡水魚類"
                else:
                    table_type = "其它類別"
                print(f"在{table_type}表格中找到{fish_name}")
                details.append(f"在{table_type}表格中找到{fish_name}")
                break
        
        if not target_table:
            status = f"在所有表格中都找不到{fish_name}"
            print(status)
            details.append(status)
            return "\n".join(details)
        
        # 獲取日期
        date_text = soup.find(string=lambda t: '本期日期：' in t)
        if not date_text:
            status = "找不到日期資訊"
            print(status)
            details.append(status)
            return "\n".join(details)
        
        print(f"找到日期文本: {date_text}")
        details.append(f"找到日期資訊: {date_text}")
        
        # 解析日期（格式：114年4月1日至114年4月30日）
        end_date = date_text.split('至')[-1].strip()
        year = int(end_date.split('年')[0]) + 1911  # 轉換為西元年
        month = int(end_date.split('年')[1].split('月')[0])
        day = int(end_date.split('月')[1].split('日')[0])
        date = datetime(year, month, day)
        print(f"解析後的日期: {date}")
        details.append(f"解析日期: {date.date()}")
        
        # 查找指定魚種資料
        rows = target_table.find_all('tr')
        print(f"在{table_type}表格中找到 {len(rows)} 行數據")
        fish_price = None
        for i, row in enumerate(rows):
            cells = row.find_all('td')
            if len(cells) >= 3:
                cell_text = cells[1].get_text().strip()
                print(f"檢查第 {i+1} 行: {cell_text}")
                if fish_name in cell_text:
                    fish_price = float(cells[2].get_text().strip())
                    print(f"找到{fish_name}價格: {fish_price}")
                    details.append(f"找到{fish_name}價格: NT$ {fish_price:.2f}")
                    break
        
        if fish_price is None:
            status = f"找不到{fish_name}價格資料"
            print(status)
            details.append(status)
            return "\n".join(details)
        
        # 如果只是要返回資料，先檢查是否重複
        if return_data_only:
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                try:
                    sql = "SELECT COUNT(*) FROM tilapia_prices WHERE date = ? AND product_name = ?"
                    cursor.execute(sql, (date.date(), fish_name))
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        return {
                            'success': False,
                            'duplicate': True,
                            'message': f"資料已存在：日期={date.date()}, 魚種={fish_name}, 價格={fish_price}",
                            'data': {
                                'date': date.date().isoformat(),
                                'fish_name': fish_name,
                                'price': fish_price
                            },
                            'details': details
                        }
                    else:
                        return {
                            'success': True,
                            'duplicate': False,
                            'data': {
                                'date': date.date().isoformat(),
                                'fish_name': fish_name,
                                'price': fish_price
                            },
                            'details': details
                        }
                finally:
                    cursor.close()
            finally:
                conn.close()
        
        # 詢問是否要儲存到資料庫
        print(f"\n找到以下資料：")
        print(f"日期：{date.date()}")
        print(f"魚種：{fish_name}")
        print(f"價格：NT$ {fish_price:.2f}")
        
        # 檢查資料是否已存在
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            try:
                sql = "SELECT COUNT(*) FROM tilapia_prices WHERE date = ? AND product_name = ?"
                cursor.execute(sql, (date.date(), fish_name))
                count = cursor.fetchone()[0]
                if count > 0:
                    status = f"資料已存在：日期={date.date()}, 魚種={fish_name}, 價格={fish_price}"
                    print(f"\n{status}")
                    details.append(status)
                    return "\n".join(details)
                
                # 根據參數決定是否詢問用戶
                if ask_confirmation:
                    # 詢問用戶是否要儲存
                    while True:
                        confirm = input("\n是否要將此資料新增到資料庫？(y/n): ").strip().lower()
                        if confirm in ['y', 'yes', '是', 'Y']:
                            print("開始保存數據到資料庫...")
                            details.append("用戶確認新增資料到資料庫...")
                            
                            sql = """
                            INSERT INTO tilapia_prices (date, product_name, avg_price)
                            VALUES (?, ?, ?)
                            """
                            cursor.execute(sql, (date.date(), fish_name, fish_price))
                            conn.commit()
                            status = f"成功儲存資料：日期={date.date()}, 魚種={fish_name}, 價格={fish_price}"
                            print(status)
                            details.append(status)
                            break
                        elif confirm in ['n', 'no', '否', 'N']:
                            status = f"用戶取消新增：日期={date.date()}, 魚種={fish_name}, 價格={fish_price}"
                            print(status)
                            details.append(status)
                            break
                        else:
                            print("請輸入 y (是) 或 n (否)")
                else:
                    # 自動儲存（用於API調用）
                    print("自動儲存資料到資料庫...")
                    details.append("自動儲存資料到資料庫...")
                    
                    sql = """
                    INSERT INTO tilapia_prices (date, product_name, avg_price)
                    VALUES (?, ?, ?)
                    """
                    cursor.execute(sql, (date.date(), fish_name, fish_price))
                    conn.commit()
                    status = f"成功儲存資料：日期={date.date()}, 魚種={fish_name}, 價格={fish_price}"
                    print(status)
                    details.append(status)
                        
            finally:
                cursor.close()
        finally:
            conn.close()
            
    except requests.exceptions.Timeout:
        print("請求超時")
        details.append("請求超時")
        status = "爬取失敗：請求超時"
    except requests.exceptions.RequestException as e:
        print(f"請求錯誤: {str(e)}")
        details.append(f"請求錯誤: {str(e)}")
        status = f"爬取失敗：請求錯誤 - {str(e)}"
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        print("詳細錯誤信息:")
        print(traceback.format_exc())
        details.append(f"發生錯誤: {str(e)}")
        status = f"爬取失敗：{str(e)}"
    
    return "\n".join(details)

if __name__ == "__main__":
    try:
        print("開始創建數據表...")
        create_table()
        print("數據表創建完成")
        
        # 從命令列參數獲取魚種名稱和模式
        fish_name = "吳郭魚"  # 默認值
        ask_confirmation = True  # 默認需要確認
        return_data_only = False  # 默認不只返回資料
        
        if len(sys.argv) > 1:
            fish_name = sys.argv[1]
            print(f"使用用戶指定的魚種：{fish_name}")
        else:
            print(f"使用默認魚種：{fish_name}")
            
        if len(sys.argv) > 2:
            mode = sys.argv[2].lower()
            if mode == 'auto':
                ask_confirmation = False
                print("自動模式：將自動儲存資料，不詢問確認")
            elif mode == 'data_only':
                return_data_only = True
                print("資料模式：只返回找到的資料，不儲存")
            else:
                print("交互模式：將詢問是否儲存資料")
        else:
            print("交互模式：將詢問是否儲存資料")
        
        status = crawl_fish_price(fish_name, ask_confirmation, return_data_only)
        
        if return_data_only:
            # 如果是資料模式，輸出JSON格式
            import json
            print(json.dumps(status, ensure_ascii=False))
        else:
            print("\n爬蟲執行狀態：")
            print("-" * 50)
            print(status)
    except Exception as e:
        print(f"程序執行出錯: {str(e)}")
        print("詳細錯誤信息:")
        print(traceback.format_exc()) 