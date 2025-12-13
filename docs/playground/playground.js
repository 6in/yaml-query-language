// YQL Playground - Main JavaScript
let pyodide;
let yqlModuleLoaded = false;
let yqlEditor;
let sqlEditor;

// サンプルYQLコード
const SAMPLES = {
    "Simple SELECT": `query:
  select:
    - id: c.id
    - name: c.name
    - email: c.email
  from: { c: customers }
  where:
    - "c.status = 'active'"
  order_by:
    - name
    - email: DESC
  limit: 10`,
    
    "Complex SELECT with Multiple JOINs": `query:
  select:
    - customer_name: c.name
    - customer_email: c.email
    - order_id: o.id
    - order_date: o.order_date
    - product_name: p.name
    - quantity: oi.quantity
    - unit_price: oi.unit_price
    - total_line_amount: "oi.quantity * oi.unit_price"
    - category_name: cat.name
  from: { c: customers }
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
    - type: INNER
      alias: oi
      table: order_items
      on: "o.id = oi.order_id"
    - type: INNER
      alias: p
      table: products
      on: "oi.product_id = p.id"
    - type: LEFT
      alias: cat
      table: categories
      on: "p.category_id = cat.id"
  where:
    - "c.status = 'active'"
    - "o.order_date >= '2024-01-01'"
    - "o.status IN ('pending', 'processing')"
  order_by:
    - order_date: DESC
    - customer_name: ASC
  limit: 50`,
    
    "Aggregation with GROUP BY and HAVING": `query:
  select:
    - customer_id: c.id
    - customer_name: c.name
    - customer_email: c.email
    - order_count: "COUNT(DISTINCT o.id)"
    - total_amount: "SUM(o.amount)"
    - average_order_amount: "AVG(o.amount)"
    - max_order_amount: "MAX(o.amount)"
    - last_order_date: "MAX(o.order_date)"
  from: { c: customers }
  joins:
    - type: LEFT
      alias: o
      table: orders
      on: "c.id = o.customer_id"
  where:
    - "c.status = 'active'"
    - "c.created_at >= '2023-01-01'"
  group_by: [c.id, c.name, c.email]
  having:
    - "COUNT(DISTINCT o.id) >= 3"
    - "SUM(o.amount) > 10000"
  order_by:
    - total_amount: DESC
  limit: 20`,
    
    "CTE with Multiple Levels": `query:
  with_clauses:
    monthly_sales:
      select:
        - customer_id: o.customer_id
        - year_month: "DATE_TRUNC('month', o.order_date)"
        - monthly_total: "SUM(o.amount)"
      from: { o: orders }
      where:
        - "o.order_date >= '2024-01-01'"
      group_by: [o.customer_id, "DATE_TRUNC('month', o.order_date)"]
    customer_rankings:
      select:
        - customer_id: ms.customer_id
        - year_month: ms.year_month
        - monthly_total: ms.monthly_total
        - rank: "RANK() OVER (PARTITION BY ms.year_month ORDER BY ms.monthly_total DESC)"
      from: { ms: monthly_sales }
  select:
    - customer_name: c.name
    - year_month: cr.year_month
    - monthly_total: cr.monthly_total
    - rank: cr.rank
  from: { cr: customer_rankings }
  joins:
    - type: INNER
      alias: c
      table: customers
      on: "cr.customer_id = c.id"
  where:
    - "cr.rank <= 10"
  order_by:
    - year_month: DESC
    - field: rank
      direction: ASC`,
    
    "Parameterized Query": `query:
  select:
    - customer_id: c.id
    - customer_name: c.name
    - order_id: o.id
    - order_date: o.order_date
    - amount: o.amount
  from: { c: customers }
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.id = o.customer_id"
  where:
    - "c.status = #{status}"
    - "o.order_date >= #{start_date}"
    - "o.order_date < #{end_date}"
    - "o.amount >= #{min_amount}"
  order_by:
    - order_date: DESC
  limit: #{limit}`,
    
    "Complex WHERE Conditions": `query:
  select:
    - product_id: p.id
    - product_name: p.name
    - category_name: c.name
    - stock_quantity: p.stock_quantity
    - price: p.price
    - discount_price: "CASE WHEN p.discount_rate > 0 THEN p.price * (1 - p.discount_rate) ELSE p.price END"
  from: { p: products }
  joins:
    - type: LEFT
      alias: c
      table: categories
      on: "p.category_id = c.id"
  where:
    - "p.status = 'active'"
    - "(p.stock_quantity > 0 OR p.allow_backorder = true)"
    - "p.price BETWEEN 100 AND 10000"
    - "(p.category_id IN (1, 2, 3) OR c.parent_category_id = 1)"
    - "p.name ILIKE '%laptop%'"
    - "p.created_at >= CURRENT_DATE - INTERVAL '1 year'"
  order_by:
    - discount_price: ASC
  limit: 100`,
    
    "Batch INSERT": `operation: insert
table: order_items
values:
  - order_id: 1001
    product_id: 201
    quantity: 2
    unit_price: 1500.00
    discount_rate: 0.1
  - order_id: 1001
    product_id: 202
    quantity: 1
    unit_price: 3000.00
    discount_rate: 0.0
  - order_id: 1001
    product_id: 203
    quantity: 3
    unit_price: 500.00
    discount_rate: 0.15
  - order_id: 1002
    product_id: 201
    quantity: 1
    unit_price: 1500.00
    discount_rate: 0.0
  - order_id: 1002
    product_id: 204
    quantity: 2
    unit_price: 2000.00
    discount_rate: 0.2`,
    
    "UPDATE with Complex Conditions": `operation: update
table: orders
set:
  status: "completed"
  completed_at: "NOW()"
  updated_at: "NOW()"
where:
  - "status = 'processing'"
  - "order_date < CURRENT_DATE - INTERVAL '7 days'"
  - "EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = orders.id AND oi.shipped_at IS NOT NULL)"`,
    
    "DELETE with JOIN-like Conditions": `operation: delete
table: customers
where:
  - "status = 'inactive'"
  - "last_login < CURRENT_DATE - INTERVAL '2 years'"
  - "NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = customers.id AND o.order_date >= CURRENT_DATE - INTERVAL '1 year')"`,
    
    "UPSERT with Conditional Update (PostgreSQL)": `operation: upsert
table: products
values:
  - id: 1001
    name: "Premium Laptop"
    price: 150000
    stock_quantity: 50
    category_id: 1
    updated_at: "NOW()"
on_conflict:
  columns: [id]
  update:
    name: "EXCLUDED.name"
    price: "EXCLUDED.price"
    stock_quantity: "products.stock_quantity + EXCLUDED.stock_quantity"
    updated_at: "NOW()"
  where: "EXCLUDED.updated_at > products.updated_at"`,
    
    "UPSERT with Multiple Rows (PostgreSQL)": `operation: upsert
table: inventory
values:
  - product_id: 201
    warehouse_id: 1
    quantity: 100
    last_restocked: "NOW()"
  - product_id: 202
    warehouse_id: 1
    quantity: 50
    last_restocked: "NOW()"
  - product_id: 201
    warehouse_id: 2
    quantity: 75
    last_restocked: "NOW()"
on_conflict:
  columns: [product_id, warehouse_id]
  update:
    quantity: "inventory.quantity + EXCLUDED.quantity"
    last_restocked: "EXCLUDED.last_restocked"`,
    
    "SELECT with Embedded Schema": `schema:
  tables:
    customers:
      columns:
        customer_id:
          type: integer
          label: "顧客ID"
          description: "顧客を一意に識別するID"
          constraints:
            primary_key: true
        name:
          type: string
          label: "顧客名"
          description: "顧客の氏名"
          max_length: 100
          constraints:
            not_null: true
        email:
          type: string
          label: "メールアドレス"
          max_length: 255
          constraints:
            not_null: true
            unique: true
        status:
          type: enum
          label: "ステータス"
          values: ["active", "inactive", "suspended"]
          default: "active"
          constraints:
            not_null: true
    
    orders:
      columns:
        order_id:
          type: integer
          label: "注文ID"
          constraints:
            primary_key: true
        customer_id:
          type: integer
          label: "顧客ID"
          constraints:
            foreign_key:
              table: "customers"
              column: "customer_id"
        order_date:
          type: date
          label: "注文日"
          constraints:
            not_null: true
        amount:
          type: decimal
          label: "注文金額"
          precision: 12
          scale: 2
          constraints:
            not_null: true
        status:
          type: enum
          label: "注文ステータス"
          values: ["pending", "confirmed", "shipped", "delivered", "cancelled"]

query:
  select:
    - customer_id: c.customer_id
    - customer_name: c.name
    - customer_email: c.email
    - customer_status: c.status
    - order_id: o.order_id
    - order_date: o.order_date
    - order_amount: o.amount
    - order_status: o.status
  from: { c: customers }
  joins:
    - type: INNER
      alias: o
      table: orders
      on: "c.customer_id = o.customer_id"
  where:
    - "c.status = 'active'"
    - "o.order_date >= '2024-01-01'"
    - "o.amount >= 1000"
  order_by:
    - order_date: DESC
    - customer_name: ASC
  limit: 50`,
};

// 初期化
async function init() {
    try {
        console.log('Initializing Monaco Editor...');
        
        // Monaco Editorの初期化（既に読み込まれている場合はスキップ）
        if (typeof monaco === 'undefined') {
            await new Promise((resolve, reject) => {
                if (typeof require === 'undefined') {
                    reject(new Error('Monaco Editor loader not found'));
                    return;
                }
                require(['vs/editor/editor.main'], resolve, reject);
            });
        }
        
        // YQLエディタの初期化
        yqlEditor = monaco.editor.create(document.getElementById('yql-editor'), {
            value: '',
            language: 'yaml',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 14,
            lineNumbers: 'on',
            wordWrap: 'on',
        });
        
        // SQLエディタの初期化（読み取り専用）
        sqlEditor = monaco.editor.create(document.getElementById('sql-output'), {
            value: '',
            language: 'sql',
            theme: 'vs-dark',
            readOnly: true,
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 14,
            lineNumbers: 'on',
            wordWrap: 'on',
        });
        
        // サンプル選択の初期化
        const sampleSelect = document.getElementById('sample-select');
        Object.keys(SAMPLES).forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            sampleSelect.appendChild(option);
        });
        
        sampleSelect.addEventListener('change', (e) => {
            const sampleName = e.target.value;
            if (sampleName && SAMPLES[sampleName]) {
                yqlEditor.setValue(SAMPLES[sampleName]);
            }
        });
        
        // Ctrl/Cmd + Enterで実行
        yqlEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, runYQL);
        
        console.log('Initializing Pyodide...');
        console.log('Checking for loadPyodide:', typeof window.loadPyodide, typeof loadPyodide);
        
        // Pyodideが読み込まれるまで待機（最大30秒）
        let pyodideLoader = window.loadPyodide;
        if (typeof pyodideLoader === 'undefined') {
            console.log('Waiting for Pyodide to load...');
            const loadingMsg = document.querySelector('#loading p');
            if (loadingMsg) loadingMsg.textContent = 'Loading Pyodide (this may take 10-20 seconds)...';
            
            await new Promise((resolve, reject) => {
                let attempts = 0;
                const maxAttempts = 300; // 30秒
                const checkPyodide = setInterval(() => {
                    attempts++;
                    pyodideLoader = window.loadPyodide;
                    if (typeof pyodideLoader !== 'undefined') {
                        clearInterval(checkPyodide);
                        console.log('Pyodide script loaded!', typeof pyodideLoader);
                        resolve();
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkPyodide);
                        reject(new Error('Pyodide failed to load within 30 seconds. Please check your internet connection and refresh the page.'));
                    } else if (attempts % 10 === 0) {
                        console.log(`Still waiting for Pyodide... (${attempts * 0.1}s)`);
                        if (loadingMsg) loadingMsg.textContent = `Loading Pyodide... (${Math.round(attempts * 0.1)}s)`;
                    }
                }, 100);
            });
        }
        
        console.log('Loading Pyodide runtime...');
        const loadingMsg = document.querySelector('#loading p');
        if (loadingMsg) loadingMsg.textContent = 'Initializing Pyodide runtime...';
        
        // Pyodideの初期化
        pyodide = await pyodideLoader({
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/",
        });
        console.log('Pyodide runtime loaded!');
        
        console.log('Pyodide loaded, installing packages...');
        
        // PyYAMLのインストール
        await pyodide.loadPackage("pyyaml");
        
        console.log('Packages installed, loading YQL module...');
        
        // YQLモジュールの読み込み
        await loadYQLModule();
        
        // 最初のサンプルを設定
        yqlEditor.setValue(SAMPLES["Simple SELECT"]);
        
        // UIイベントの設定
        document.getElementById('run-btn').addEventListener('click', runYQL);
        document.getElementById('clear-btn').addEventListener('click', clearEditor);
        
        // ローディング画面を非表示
        document.getElementById('loading').style.display = 'none';
        document.getElementById('editor-container').style.display = 'flex';
        
        console.log('✅ YQL Playground ready!');
    } catch (error) {
        console.error('Initialization error:', error);
        document.getElementById('loading').innerHTML = 
            `<p style="color: red;">Error: ${error.message}</p>`;
    }
}

// YQLモジュールの読み込み
async function loadYQLModule() {
    try {
        // YQLバンドルファイル（tar.gz）を読み込む（キャッシュ回避のためタイムスタンプを追加）
        const timestamp = new Date().getTime();
        const response = await fetch(`yql-bundle.tar.gz?v=${timestamp}`, {
            cache: 'no-cache'
        });
        if (!response.ok) {
            throw new Error(`Failed to load yql-bundle.tar.gz: ${response.statusText}`);
        }
        
        const arrayBuffer = await response.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        
        // Pyodideの仮想ファイルシステムにtar.gzを書き込む
        pyodide.FS.writeFile('/yql-bundle.tar.gz', uint8Array);
        
        // Pythonでtar.gzを解凍して仮想ファイルシステムに展開
        pyodide.runPython(`
import tarfile
import sys
from pathlib import Path

# tar.gzを解凍
with tarfile.open('/yql-bundle.tar.gz', 'r:gz') as tar:
    tar.extractall('/')

# sys.pathに追加（srcディレクトリを追加）
sys.path.insert(0, '/')

# yqlモジュールをインポートして確認
import yql
print(f'✅ YQL module loaded: {yql.__version__}')
        `);
        
        yqlModuleLoaded = true;
        
        console.log('✅ YQL module loaded');
    } catch (error) {
        console.error('Error loading YQL module:', error);
        throw error;
    }
}

// YQLコードの実行
async function runYQL() {
    if (!yqlModuleLoaded) {
        alert('YQL module is still loading... Please wait.');
        return;
    }
    
    const yqlCode = yqlEditor.getValue().trim();
    if (!yqlCode) {
        alert('Please enter YQL code.');
        return;
    }
    
    const dialect = document.getElementById('dialect').value;
    const runBtn = document.getElementById('run-btn');
    
    // 実行中状態
    runBtn.disabled = true;
    runBtn.textContent = 'Running...';
    sqlEditor.setValue('Running...');
    sqlEditor.updateOptions({ theme: 'vs-dark' });
    
    try {
        const pythonCode = `
from yql import parse, generate_sql, Dialect
import json
import traceback

yql_content = ${JSON.stringify(yqlCode)}
dialect_name = ${JSON.stringify(dialect)}

try:
    query = parse(yql_content)
    dialect_enum = getattr(Dialect, dialect_name.upper())
    sql = generate_sql(query, dialect_enum)
    result = {"status": "success", "sql": sql}
except Exception as e:
    error_msg = str(e)
    traceback_str = traceback.format_exc()
    result = {"status": "error", "message": error_msg, "traceback": traceback_str}

json.dumps(result)
        `;
        
        const resultJson = pyodide.runPython(pythonCode);
        const result = JSON.parse(resultJson);
        
        if (result.status === 'success') {
            sqlEditor.setValue(result.sql);
            sqlEditor.updateOptions({ theme: 'vs-dark' });
        } else {
            // エラーメッセージを整形
            const errorText = formatError(result.message, result.traceback);
            sqlEditor.setValue(errorText);
            sqlEditor.updateOptions({ theme: 'vs-dark' });
        }
    } catch (error) {
        sqlEditor.setValue(`JavaScript Error: ${error.message}`);
        sqlEditor.updateOptions({ theme: 'vs-dark' });
        console.error('Execution error:', error);
    } finally {
        runBtn.disabled = false;
        runBtn.textContent = 'Run';
    }
}

// エラーメッセージを整形
function formatError(message, traceback) {
    // エラーカテゴリを判定
    let category = 'syntax_error';
    let emoji = '❌';
    
    if (message.includes('Invalid') && message.includes('Valid')) {
        category = 'syntax_error';
        emoji = '📝';
    } else if (message.includes('Circular dependency') || message.includes('Import')) {
        category = 'logic_error';
        emoji = '🔗';
    } else if (message.includes('security') || message.includes('Security')) {
        category = 'security_error';
        emoji = '🔒';
    }
    
    let formatted = `${emoji} ${category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${message}\n\n`;
    
    // パーサーエラーの場合、より分かりやすく表示
    if (message.includes('Invalid') && message.includes('Valid')) {
        formatted += `💡 ${message}\n\n`;
    }
    
    // トレースバックを簡潔に表示
    if (traceback) {
        const lines = traceback.split('\n');
        // 重要な行だけを抽出（File行とエラーメッセージ行）
        const importantLines = lines.filter(line => 
            line.includes('File') || 
            line.includes('Error') || 
            line.includes('ParseError') ||
            line.trim().startsWith('^')
        );
        
        if (importantLines.length > 0) {
            formatted += '📋 Details:\n';
            formatted += importantLines.slice(0, 5).join('\n');
        }
    }
    
    return formatted;
}

// エディタのクリア
function clearEditor() {
    if (confirm('Clear the editor?')) {
        yqlEditor.setValue('');
        sqlEditor.setValue('');
    }
}

// ページ読み込み時に初期化（Pyodideの読み込み完了を待つ）
if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', () => {
        // Pyodideが読み込まれるまで少し待つ
        setTimeout(init, 100);
    });
} else {
    // 既に読み込み完了している場合
    setTimeout(init, 100);
}
