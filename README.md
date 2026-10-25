# FCU Grade Exporter

自動擷取逢甲大學 MyFCU 歷年學期成績，並整合成 Excel 檔案。

## 使用方式

### 1. 下載專案

```bash
git clone <你的 GitHub Repository URL>
cd fcu-grade-exporter
```

也可以在 GitHub 點選 **Code → Download ZIP**，解壓縮後進入專案資料夾。

### 2. 建立虛擬環境

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows（PowerShell）**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 安裝套件與瀏覽器

```bash
python -m pip install playwright beautifulsoup4 openpyxl
python -m playwright install chromium
```

### 4. 設定 MyFCU 帳號

在專案根目錄新增 `credentials.txt`：

```ini
username=你的MyFCU帳號
password=你的MyFCU密碼
```

請使用自己的帳號，**不要將 `credentials.txt` 上傳到 GitHub**。

### 5. 執行程式

```bash
python main.py
```

程式將依序：

1. 讀取 `credentials.txt` 並登入 MyFCU。
2. 查詢並儲存各學期成績 HTML。
3. 合併成績並輸出 Excel。

若學校要求額外驗證，請依瀏覽器畫面完成操作。

## 輸出檔案

執行完成後：

```text
fcu-grade-exporter/
├── main.py
├── grade_scraper.py
├── excel_exporter.py
├── credentials.txt
├── semester_html/
│   ├── semester_111_1.html
│   ├── semester_111_2.html
│   └── ...
└── fcu_grades.xlsx
```

- `semester_html/`：各學期的成績 HTML。
- `fcu_grades.xlsx`：合併後的歷年成績，依學年度與學期由舊到新排列。

如果已經下載過 HTML，只想重新產生 Excel：

```bash
python excel_exporter.py
```

> 本工具為非官方個人專案，僅供本人帳號的成績整理使用。匯出的 Excel 並非學校正式成績單。
