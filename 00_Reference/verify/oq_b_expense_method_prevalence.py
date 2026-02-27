"""
OQ-B: What fraction of KOSDAQ companies use "nature of expense" (성격별 분류)
vs "function of expense" (기능별 분류) income statement presentation?

Requires DART_API_KEY in .env.
Makes ~50 API calls (~25 seconds at 0.5s delay).
"""
import sys
import time
import random
import pandas as pd
from verify_utils import get_dart, RESULTS_DIR

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SAMPLE_SIZE = 50
SLEEP_BETWEEN = 0.5  # seconds


def main():
    dart = get_dart()

    print("Fetching KOSDAQ ticker list from PyKRX...")
    from pykrx import stock
    tickers = stock.get_market_ticker_list("20241230", market="KOSDAQ")
    print(f"Total KOSDAQ tickers: {len(tickers)}")

    print("Loading DART corp_codes...")
    corp_df = dart.corp_codes
    # corp_codes has columns: corp_code, corp_name, corp_eng_name, stock_code, modify_date
    corp_df = corp_df[corp_df["stock_code"].notna() & (corp_df["stock_code"] != "")]

    kosdaq_set = set(tickers)
    kosdaq_corps = corp_df[corp_df["stock_code"].isin(kosdaq_set)].copy()
    print(f"DART corp_codes matched to KOSDAQ: {len(kosdaq_corps)}")

    sample = kosdaq_corps.sample(min(SAMPLE_SIZE, len(kosdaq_corps)), random_state=42)
    print(f"Sample size: {len(sample)}")
    print()

    results = []
    for i, (_, row) in enumerate(sample.iterrows(), 1):
        corp_code = row["corp_code"]
        corp_name = row["corp_name"]
        stock_code = row["stock_code"]
        status = "unknown"
        try:
            df = dart.finstate_all(corp_code, 2023, fs_div="CFS")
            if df is None or df.empty:
                status = "empty_response"
            else:
                # Income statement rows appear under sj_div='IS' or 'CIS' (combined format)
                if "sj_div" in df.columns:
                    is_stmts = df[df["sj_div"].isin(["IS", "CIS"])]
                else:
                    is_stmts = df
                account_names = is_stmts["account_nm"].str.strip().tolist() if "account_nm" in is_stmts.columns else []
                if "매출원가" in account_names:
                    status = "function_method"
                elif len(is_stmts) > 0:
                    status = "nature_method"
                else:
                    status = "no_is_rows"
        except Exception as e:
            status = f"error: {e}"

        results.append({
            "corp_code": corp_code,
            "corp_name": corp_name,
            "stock_code": stock_code,
            "status": status,
        })
        print(f"[{i:3d}/{len(sample)}] {stock_code} {corp_name[:20]:<20} → {status}")
        time.sleep(SLEEP_BETWEEN)

    df_results = pd.DataFrame(results)
    counts = df_results["status"].value_counts()
    total = len(df_results)

    print()
    print("=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    for status, count in counts.items():
        print(f"  {status:<25} {count:3d}  ({count/total*100:.1f}%)")
    print()

    function_n = counts.get("function_method", 0)
    nature_n = counts.get("nature_method", 0)
    valid = function_n + nature_n
    if valid > 0:
        print(f"Among companies with valid IS data ({valid}):")
        print(f"  Function method (기능별): {function_n} ({function_n/valid*100:.1f}%)")
        print(f"  Nature method  (성격별): {nature_n} ({nature_n/valid*100:.1f}%)")
    print()

    out_path = RESULTS_DIR / "oq_b_expense_method.csv"
    df_results.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
