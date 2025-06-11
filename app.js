const express = require('express');
const path = require('path');
const { spawn } = require('child_process');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const port = 3000;

// 靜態文件服務
app.use(express.static('public'));
app.use(express.json()); // 添加JSON解析中間件

// 添加 CORS 支持
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

// 建立資料庫連接
const db = new sqlite3.Database(path.join(__dirname, 'db', 'prices.db'), (err) => {
  if (err) {
    console.error('資料庫連接錯誤:', err);
  } else {
    console.log('成功連接到 SQLite 資料庫');
  }
});

// 執行爬蟲 - 只獲取資料，不儲存
app.post('/api/crawler/get-data', async (req, res) => {
    try {
        const { fishName } = req.body;
        console.log(`開始執行爬蟲獲取資料，搜尋魚種：${fishName || '吳郭魚'}...`);
        
        // 將魚種名稱和資料模式作為參數傳遞給Python腳本
        const args = ['fish_price_crawler/crawler.py'];
        if (fishName) {
            args.push(fishName);
        }
        args.push('data_only'); // 只返回資料，不儲存
        const pythonProcess = spawn('python', args);
        
        let output = '';
        let errorOutput = '';
        
        pythonProcess.stdout.on('data', (data) => {
            const chunk = data.toString();
            console.log('爬蟲輸出:', chunk);
            output += chunk;
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const chunk = data.toString();
            console.error('爬蟲錯誤:', chunk);
            errorOutput += chunk;
        });
        
        await new Promise((resolve, reject) => {
            pythonProcess.on('close', (code) => {
                console.log(`爬蟲進程退出，退出碼: ${code}`);
                if (code === 0) {
                    try {
                        // 嘗試解析JSON輸出
                        const lines = output.trim().split('\n');
                        const lastLine = lines[lines.length - 1];
                        const crawlerResult = JSON.parse(lastLine);
                        resolve(crawlerResult);
                    } catch (parseError) {
                        console.error('解析爬蟲輸出失敗:', parseError);
                        resolve({ success: false, error: '解析爬蟲輸出失敗', output: output });
                    }
                } else {
                    reject(new Error(`爬蟲執行失敗，退出碼：${code}\n${errorOutput}`));
                }
            });
        }).then(result => {
            res.json(result);
        }).catch(error => {
            console.error('爬蟲執行錯誤:', error);
            res.status(500).json({ 
                success: false,
                error: `爬蟲執行失敗: ${error.message}`,
                errorOutput: errorOutput
            });
        });
        
    } catch (error) {
        console.error('執行爬蟲時發生錯誤:', error);
        res.status(500).json({ 
            status: `執行爬蟲時發生錯誤: ${error.message}`,
            error: error.stack
        });
    }
});

// 儲存確認的爬蟲資料
app.post('/api/crawler/save-data', (req, res) => {
    try {
        const { date, fish_name, price } = req.body;
        console.log('儲存確認的資料:', { date, fish_name, price });
        
        // 檢查資料是否已存在
        const checkSql = 'SELECT COUNT(*) as count FROM tilapia_prices WHERE date = ? AND product_name = ?';
        db.get(checkSql, [date, fish_name], (err, result) => {
            if (err) {
                console.error('檢查資料失敗:', err);
                res.status(500).json({ error: '檢查資料失敗' });
                return;
            }
            
            if (result.count > 0) {
                res.json({ 
                    success: false, 
                    message: `資料已存在：日期=${date}, 魚種=${fish_name}` 
                });
                return;
            }
            
            // 插入新資料
            const insertSql = 'INSERT INTO tilapia_prices (date, product_name, avg_price) VALUES (?, ?, ?)';
            db.run(insertSql, [date, fish_name, price], function(err) {
                if (err) {
                    console.error('儲存資料失敗:', err);
                    res.status(500).json({ error: '儲存資料失敗' });
                    return;
                }
                
                res.json({ 
                    success: true, 
                    message: `成功儲存資料：日期=${date}, 魚種=${fish_name}, 價格=${price}`,
                    id: this.lastID
                });
            });
        });
        
    } catch (error) {
        console.error('儲存資料時發生錯誤:', error);
        res.status(500).json({ 
            error: `儲存資料時發生錯誤: ${error.message}`
        });
    }
});

// 獲取價格數據
app.get('/api/prices', (req, res) => {
  console.log('開始獲取價格數據...');
  const { limit = 20, startDate, endDate } = req.query;
  console.log('查詢參數:', { limit, startDate, endDate });
  
  let sql = 'SELECT date, product_name, avg_price FROM tilapia_prices';
  const params = [];
  
  if (startDate || endDate) {
    sql += ' WHERE';
    if (startDate) {
      sql += ' date >= ?';
      params.push(startDate);
    }
    if (startDate && endDate) {
      sql += ' AND';
    }
    if (endDate) {
      sql += ' date <= ?';
      params.push(endDate);
    }
  }
  
  sql += ' ORDER BY date DESC';
  if (limit) {
    sql += ' LIMIT ?';
    params.push(parseInt(limit));
  }
  
  db.all(sql, params, (err, rows) => {
    if (err) {
      console.error('獲取數據失敗:', err);
      res.status(500).json({ error: '獲取數據失敗' });
      return;
    }
    
    const records = rows.map(row => ({
      date: row.date,
      product_name: row.product_name,
      avg_price: row.avg_price
    }));
    
    // 獲取總記錄數
    let countSql = 'SELECT COUNT(*) as total FROM tilapia_prices';
    const countParams = [];
    
    if (startDate || endDate) {
      countSql += ' WHERE';
      if (startDate) {
        countSql += ' date >= ?';
        countParams.push(startDate);
      }
      if (startDate && endDate) {
        countSql += ' AND';
      }
      if (endDate) {
        countSql += ' date <= ?';
        countParams.push(endDate);
      }
    }
    
    db.get(countSql, countParams, (err, result) => {
      if (err) {
        console.error('獲取記錄總數失敗:', err);
        res.status(500).json({ error: '獲取記錄總數失敗' });
        return;
      }
      
      res.json({
        records,
        total: result.total,
        limit: parseInt(limit)
      });
    });
  });
});

// 搜索價格數據
app.get('/api/prices/search', (req, res) => {
  console.log('開始搜索價格數據...');
  const { term, startDate, endDate } = req.query;
  console.log('搜索參數:', { term, startDate, endDate });
  
  if (!term) {
    return res.status(400).json({ error: '請提供搜尋關鍵字' });
  }
  
  let sql = 'SELECT date, product_name, avg_price FROM tilapia_prices WHERE product_name LIKE ?';
  const params = [`%${term}%`];
  
  if (startDate) {
    sql += ' AND date >= ?';
    params.push(startDate);
  }
  if (endDate) {
    sql += ' AND date <= ?';
    params.push(endDate);
  }
  
  sql += ' ORDER BY date DESC';
  
  db.all(sql, params, (err, rows) => {
    if (err) {
      console.error('搜索數據失敗:', err);
      res.status(500).json({ error: '搜索數據失敗' });
      return;
    }
    
    const records = rows.map(row => ({
      date: row.date,
      product_name: row.product_name,
      avg_price: row.avg_price
    }));
    
    res.json({
      records,
      total: records.length
    });
  });
});

// 啟動服務器
app.listen(port, () => {
  console.log(`服務器運行在 http://localhost:${port}`);
});
