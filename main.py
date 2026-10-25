from pathlib import Path
import subprocess
import sys
import time


BASE_DIR = Path(__file__).resolve().parent

READ_WEBSITE = BASE_DIR / "grade_scraper.py"
HTML_TO_EXCEL = BASE_DIR / "excel_exporter.py"


def run_script(script_path):
    """
    使用目前虛擬環境的 Python 執行指定程式。
    """

    if not script_path.exists():
        raise FileNotFoundError(
            f"找不到程式：{script_path}"
        )

    print("\n" + "=" * 60, flush=True)
    print(f"開始執行：{script_path.name}", flush=True)
    print("=" * 60, flush=True)

    start_time = time.time()

    # 執行子程式，並等待執行完成
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
        check=True
    )

    elapsed = time.time() - start_time

    print(
        f"\n{script_path.name} 執行完成！"
        f"耗時：{elapsed:.2f} 秒",
        flush=True
    )


def main():

    print("\n" + "=" * 60)
    print("FCU 歷年學期成績自動下載與 Excel 整合系統")
    print("=" * 60)

    try:

        # STEP 1：登入 MyFCU，下載所有學期 HTML
        run_script(READ_WEBSITE)

        # STEP 2：合併所有學期成績到 Excel
        run_script(HTML_TO_EXCEL)

        print("\n" + "=" * 60)
        print("所有工作執行完成！")
        print("=" * 60)

        print(f"\nExcel：{BASE_DIR / '歷年學期成績.xlsx'}")

    except subprocess.CalledProcessError as e:

        print(
            f"\n執行失敗：{e.cmd}"
            f"\n結束代碼：{e.returncode}"
        )

    except Exception as e:

        print(f"\n發生錯誤：{e}")


if __name__ == "__main__":
    main()