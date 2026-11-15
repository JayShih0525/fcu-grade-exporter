from pathlib import Path
import sys
from progress import report_progress
from playwright.sync_api import sync_playwright
import csv
import re
import time


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

USER_INFO_FILE = BASE_DIR / "credentials.txt"

OUTPUT_DIR = BASE_DIR / "semester_html"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOGIN_URL = (
    "https://myfcu.fcu.edu.tw/main/"
    "InfoMyFcuLogin.aspx#/prog/home"
)

GRADE_URL = (
    "https://myfcu.fcu.edu.tw/main/"
    "webClientMyFcuMain.aspx#!/prog/SP400311"
)

GRADE_FRAME_KEYWORD = "S360381_score.aspx"

BUTTON_TEXT = "查詢學期成績"

BUTTON_SELECTOR = (
    "button, "
    "input[type='button'], "
    "input[type='submit'], "
    "a, "
    "[role='button']"
)

FRAME_TIMEOUT = 60
PAGE_TIMEOUT = 20000


# ============================================================
# Read user credentials
# ============================================================

def read_user_info():
    """
    從 credentials.txt 讀取帳號密碼。

    格式：
        username=...
        password=...
    """

    if not USER_INFO_FILE.exists():
        raise FileNotFoundError(
            f"找不到帳號密碼檔案：{USER_INFO_FILE}"
        )

    data = {}

    with USER_INFO_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            data[key.strip().lower()] = value.strip()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise ValueError(
            "credentials.txt 必須包含 username 和 password"
        )

    print("成功讀取 credentials.txt")

    return username, password


# ============================================================
# Login
# ============================================================

def login_myfcu(page, username, password):
    """
    自動登入 MyFCU。

    1. 開啟登入頁面
    2. 點擊右上角登入按鈕
    3. 等待登入視窗顯示
    4. 填入帳號密碼
    5. 點擊 Login
    6. 等待登入完成
    """

    print("\n" + "=" * 60)
    print("STEP 1：登入 MyFCU")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. 開啟登入頁面
    # --------------------------------------------------------

    page.goto(
        LOGIN_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    print("已開啟 MyFCU 登入頁面")

    # --------------------------------------------------------
    # 2. 點擊右上角登入按鈕
    # --------------------------------------------------------

    print("正在開啟登入視窗...")

    login_menu = page.locator(
        "div[ng-click='switchBalloon()']"
    )

    login_menu.wait_for(
        state="visible",
        timeout=20000
    )

    login_menu.click()

    print("已點擊右上角登入按鈕")

    # --------------------------------------------------------
    # 3. 等待登入欄位顯示
    # --------------------------------------------------------

    username_input = page.locator("#txtUserName")
    password_input = page.locator("#txtPassword")

    username_input.wait_for(
        state="visible",
        timeout=20000
    )

    password_input.wait_for(
        state="visible",
        timeout=20000
    )

    print("登入視窗已顯示")

    # --------------------------------------------------------
    # 4. 填入帳號密碼
    # --------------------------------------------------------

    time.sleep(0.5)

    username_input.fill(username)

    password_input.fill(password)

    print("已填入帳號密碼")

    # --------------------------------------------------------
    # 5. 點擊 Login
    # --------------------------------------------------------

    login_button = page.locator("#OKButton")

    login_button.click(timeout=10000)

    print("已送出登入請求")

    # --------------------------------------------------------
    # 6. 等待登入結果
    # --------------------------------------------------------

    print("正在等待登入完成...")

    try:

        page.wait_for_url(
            lambda url: "InfoMyFcuLogin.aspx" not in url,
            timeout=20000
        )

        print("登入後已離開登入頁面")

    except Exception as exc:
        raise RuntimeError(
            "自動登入未完成，請確認帳號密碼；若網站要求額外驗證，無法自動略過。"
        ) from exc

    print("登入階段完成")


# ============================================================
# Navigate to grade page
# ============================================================

def open_grade_page(page):
    """
    前往 MyFCU 成績查詢頁面。
    """

    print("\n" + "=" * 60)
    print("STEP 2：前往學期成績查詢")
    print("=" * 60)

    page.goto(
        GRADE_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    print(f"目前網址：{page.url}")


# ============================================================
# Find grade iframe
# ============================================================

def get_grade_frame(page, timeout=FRAME_TIMEOUT):
    """
    等待成績查詢 iframe 出現。
    """

    start_time = time.monotonic()

    while time.monotonic() - start_time < timeout:

        for frame in page.frames:

            if GRADE_FRAME_KEYWORD in frame.url:

                return frame

        page.wait_for_timeout(500)

    raise RuntimeError(
        "找不到成績查詢 iframe，請確認已成功登入。"
    )


# ============================================================
# Find semester buttons
# ============================================================

def get_buttons(frame):
    """
    搜尋所有可見的查詢學期成績按鈕。
    """

    locator = frame.locator(BUTTON_SELECTOR)

    buttons = []

    for i in range(locator.count()):

        element = locator.nth(i)

        try:

            text = element.inner_text(
                timeout=1000
            ).strip()

            value = element.get_attribute("value") or ""

            if (
                BUTTON_TEXT in text
                or BUTTON_TEXT in value
            ):

                if element.is_visible():
                    buttons.append(element)

        except Exception:
            continue

    return buttons


# ============================================================
# Wait for list
# ============================================================

def wait_for_list(page, timeout=PAGE_TIMEOUT):

    start_time = time.monotonic()

    while (time.monotonic() - start_time) * 1000 < timeout:

        frame = get_grade_frame(page, timeout=5)

        if "#/list" in frame.url:

            buttons = get_buttons(frame)

            if buttons:
                return frame

        page.wait_for_timeout(500)

    raise RuntimeError("等待學期列表逾時")


# ============================================================
# Wait for detail
# ============================================================

def wait_for_detail(page, timeout=PAGE_TIMEOUT):

    start_time = time.monotonic()

    while (time.monotonic() - start_time) * 1000 < timeout:

        frame = get_grade_frame(page, timeout=5)

        if "#/detail/" in frame.url:
            return frame

        page.wait_for_timeout(500)

    raise RuntimeError("等待成績明細頁面逾時")


# ============================================================
# Return to list
# ============================================================

def return_to_list(page):

    frame = get_grade_frame(page)

    if "#/list" not in frame.url:

        frame.evaluate(
            "() => { window.location.hash = '#/list'; }"
        )

    return wait_for_list(page)


# ============================================================
# Save HTML
# ============================================================

def save_grade_html(frame, index):

    url = frame.url

    match = re.search(
        r"#/detail/(\d+)/(\d+)",
        url
    )

    if match:

        year = match.group(1)
        semester = match.group(2)

        filename = (
            f"semester_{year}_{semester}.html"
        )

    else:

        year = ""
        semester = ""

        filename = f"semester_{index}.html"

    filepath = OUTPUT_DIR / filename

    filepath.write_text(
        frame.content(),
        encoding="utf-8"
    )

    print(f"已儲存：{filename}")

    return {
        "button_index": index,
        "year": year,
        "semester": semester,
        "url": url,
        "filename": str(filepath),
        "status": "success"
    }


# ============================================================
# Save summary
# ============================================================

def save_summary(results):

    filepath = OUTPUT_DIR / "summary.csv"

    fields = [
        "button_index",
        "year",
        "semester",
        "url",
        "filename",
        "status"
    ]

    with filepath.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"\n已儲存：{filepath}")


# ============================================================
# Process all semesters
# ============================================================

def process_semesters(page):

    results = []

    frame = return_to_list(page)

    buttons = get_buttons(frame)

    total = len(buttons)

    print("\n" + "=" * 60)
    print(f"找到 {total} 個查詢學期成績按鈕")
    print("=" * 60)

    for completed, index in enumerate(range(total - 1, -1, -1), start=1):

        button_number = index + 1

        print(
            f"\n正在處理第 {button_number}/{total} 個學期..."
        )

        try:

            # 返回列表
            frame = return_to_list(page)

            # 重新取得按鈕
            buttons = get_buttons(frame)

            if index >= len(buttons):

                print("按鈕數量改變，跳過")

                results.append({
                    "button_index": button_number,
                    "year": "",
                    "semester": "",
                    "url": "",
                    "filename": "",
                    "status": "button_missing"
                })

                continue

            # 點擊按鈕
            buttons[index].click(timeout=10000)

            # 等待明細頁面
            detail_frame = wait_for_detail(page)

            print(f"進入：{detail_frame.url}")

            # 等待 AngularJS 完成載入課程資料，避免儲存空白表格。
            detail_frame.wait_for_function(
                """() => {
                    const rows = document.querySelectorAll(
                        'tr[ng-repeat="item in slistCtrl.semesterScoreList.list"]'
                    );
                    return Array.from(rows).some(row => {
                        const cells = row.querySelectorAll('td');
                        return cells.length === 9 &&
                            /^\\d+$/.test(cells[0].textContent.trim()) &&
                            cells[3].textContent.trim() !== '' &&
                            !row.textContent.includes('{{');
                    });
                }""",
                timeout=PAGE_TIMEOUT,
            )

            detail_frame = get_grade_frame(page)

            # 儲存 HTML
            result = save_grade_html(
                detail_frame,
                button_number
            )

            results.append(result)

            print("完成")

        except Exception as e:

            print(f"發生錯誤：{e}")

            results.append({
                "button_index": button_number,
                "year": "",
                "semester": "",
                "url": "",
                "filename": "",
                "status": "failed"
            })

            try:
                return_to_list(page)

            except Exception:
                print("無法返回列表，停止執行")
                break

        finally:
            report_progress(20 + 75 * completed / total,
                            f"已處理 {completed}/{total} 個學期")

    return results


# ============================================================
# Main
# ============================================================

def main():

    report_progress(0, "開始背景執行")
    # 讀取帳號密碼
    username, password = read_user_info()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            slow_mo=0
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 900
            }
        )

        page = context.new_page()

        try:

            # STEP 1：登入
            login_myfcu(
                page,
                username,
                password
            )

            report_progress(10, "登入完成")

            # STEP 2：進入成績查詢
            open_grade_page(page)

            # STEP 3：等待 iframe
            frame = get_grade_frame(
                page,
                timeout=60
            )

            print("\n成功找到成績查詢系統")
            print(frame.url)

            report_progress(20, "已開啟學期列表")

            # STEP 4：讀取所有學期
            results = process_semesters(page)

            # STEP 5：儲存結果
            save_summary(results)

            success_count = sum(
                1 for result in results
                if result["status"] == "success"
            )

            print("\n" + "=" * 60)
            print("執行完成")
            print("=" * 60)

            print(f"成功處理：{success_count} 個學期")
            print(f"總處理數：{len(results)}")

            for result in results:

                print(
                    f"按鈕 {result['button_index']} | "
                    f"學年度 {result['year']} | "
                    f"學期 {result['semester']} | "
                    f"{result['status']}"
                )

            if not results or success_count != len(results):
                raise RuntimeError("部分學期下載失敗，已停止匯出，請查看 summary.csv。")
            report_progress(100, "所有學期下載完成")

        except Exception as e:

            print(f"\n程式執行失敗：{e}", flush=True)
            raise

        finally:

            browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr, flush=True)
        sys.exit(1)