# 期末專題 通貨膨脹 你關心蛋嗎?

## 作品連結
[github.com/mdwiwi0130/WebFinalProjectD1211450](https://github.com/mdwiwi0130/WebFinalProjectD1211450)

## 專案介紹

這是一個專為農產品價格追蹤設計的系統，特別針對吳郭魚價格進行監控。選擇吳郭魚作為追蹤商品的原因如下：

1. **民生必需品**：吳郭魚是台灣重要的食用魚種，價格波動直接影響民眾日常生活
2. **價格敏感度高**：受季節、氣候、供需等因素影響，價格變化明顯
3. **市場透明度需求**：幫助消費者了解市場行情，做出更明智的購買決策
4. **產業價值**：協助養殖業者掌握市場趨勢，優化生產規劃

## 系統架構

### 前端技術
- HTML5
- CSS3 (Flexbox, Grid)
- JavaScript (ES6+)
- Chart.js (圖表視覺化)

### 後端技術
- Node.js
- Express.js
- SQLite (資料庫)

## 教學說明

### 前置準備

1. **安裝必要工具**
   - Node.js (建議版本 14.0.0 以上)
   - Git
   - 程式碼編輯器 (如 VS Code)

2. **取得程式碼**
   ```bash
   git clone https://github.com/mdwiwi0130/web_wk4.git
   cd web_wk4
   ```

### 系統架設步驟

1. **安裝依賴套件**
   ```bash
   npm install
   ```
   這會安裝所有必要的套件，包括：
   - express：網頁伺服器框架
   - sqlite3：資料庫
   - chart.js：圖表視覺化
   - 其他必要套件

2. **啟動伺服器**
   ```bash
   npm start
   ```
   伺服器會在 http://localhost:3000 啟動

### 功能說明

1. **手動輸入資料**
   - 從[漁產品批發市場交易行情站](https://efish.fa.gov.tw/efish/statistics/trendchart.htm)下載資料
   ![行情走勢圖](https://hackmd.io/_uploads/ryQ-4gwzlx.png)
   - 將民國年轉換為西元年（使用當月30日）
   - 整理資料格式：
     ```sql
     ('2024.1.30', '吳郭魚', 55.5),
     ('2024.2.30', '吳郭魚', 59.3),
     ('2024.3.30', '吳郭魚', 64.4),
     ('2024.4.30', '吳郭魚', 62.8);
     ```
   - 在系統中逐筆輸入資訊
   ![手動輸入](https://hackmd.io/_uploads/SJbBFxDMeg.png)

2. **自動爬蟲功能**
   - 點擊「自動取得吳郭魚價格」按鈕
   - 系統自動從[漁產品批發市場交易行情站](https://efish.fa.gov.tw/efish/statistics/simplechart.htm)爬取當前價格
   - 自動儲存至資料庫
   ![自動爬蟲](https://hackmd.io/_uploads/BJ9q9gvfge.png)

3. **查詢功能**
   - 基本查詢：顯示最新20筆記錄
   - 進階查詢：
     - 使用商品名稱搜尋特定商品
     - 選擇時間區段查看歷史價格
     - 自動生成價格趨勢圖
   ![查詢功能](https://hackmd.io/_uploads/HyQw2xPGlx.png)
   ![時間區段查詢](https://hackmd.io/_uploads/Bki1pePMex.png)

### 技術實作說明

1. **資料庫結構**
   ```sql
   CREATE TABLE prices (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     date TEXT NOT NULL,
     product_name TEXT NOT NULL,
     avg_price REAL NOT NULL
   );
   ```

2. **API 端點**
   - GET /api/prices：取得價格記錄
   - POST /api/prices：新增價格記錄
   - GET /api/prices/search：搜尋價格記錄
   - POST /api/crawler/run：執行爬蟲

3. **爬蟲功能**
   ```javascript
   async function runCrawler() {
     try {
       const response = await axios.get('https://efish.fa.gov.tw/efish/statistics/simplechart.htm');
       // 解析網頁內容
       // 提取價格資訊
       // 儲存至資料庫
     } catch (error) {
       console.error('爬蟲執行錯誤:', error);
     }
   }
   ```

### 常見問題解決

1. **伺服器無法啟動**
   - 檢查 Node.js 版本
   - 確認所有套件都已正確安裝
   - 檢查 3000 端口是否被占用

2. **爬蟲失敗**
   - 確認網路連線
   - 檢查目標網站是否可訪問
   - 查看錯誤日誌

3. **資料庫錯誤**
   - 確認資料庫檔案權限
   - 檢查 SQL 語法
   - 驗證資料格式

## 參考來源
- [漁產品批發市場交易行情站](https://efish.fa.gov.tw/efish/statistics/simplechart.htm)

## 更新紀錄

- **無障礙性改進**：
  - 修正 ARIA 角色結構，確保標籤頁和面板的關係正確
  - 添加適當的 `aria-label` 和 `aria-required` 屬性
  - 改進表單和按鈕的無障礙性標籤
  - 優化螢幕閱讀器支援
  ![](lighthouse.png)

- **效能優化**：
  - 添加 viewport meta 標籤，優化行動裝置顯示
  - 延遲載入非關鍵資源（Chart.js）
  - 優化 CSS 和 JavaScript 載入順序
  - 添加 SEO 相關的 meta 標籤

- **使用者體驗改進**：
  - 改進標籤頁切換邏輯
  - 優化表單驗證和錯誤處理
  - 添加更多使用者回饋機制
  - 改進搜尋功能的響應性
