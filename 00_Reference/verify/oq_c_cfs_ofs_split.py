"""
OQ-C: What fraction of KOSDAQ companies file Consolidated Financial Statements
(CFS) vs OFS only?

Requires DART_API_KEY in .env.
Makes ~200 API calls (~100 seconds at 0.5s delay).
"""
import sys
import time
import pandas as pd
from verify_utils import get_dart, RESULTS_DIR

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SAMPLE_SIZE = 200
SLEEP_BETWEEN = 0.5


def main():
    dart = get_dart()

    print("Fetching KOSDAQ ticker list from PyKRX...")
    from pykrx import stock
    tickers = stock.get_market_ticker_list("20221230", market="KOSDAQ")
    print(f"Total KOSDAQ tickers: {len(tickers)}")

    print("Loading DART corp_codes...")
    corp_df = dart.corp_codes
    corp_df = corp_df[corp_df["stock_code"].notna() & (corp_df["stock_code"] != "")]

    kosdaq_set = set(tickers)
    kosdaq_corps = corp_df[corp_df["stock_code"].isin(kosdaq_set)].copy()
    print(f"DART corp_codes matched to KOSDAQ: {len(kosdaq_corps)}")

    sample = kosdaq_corps.sample(min(SAMPLE_SIZE, len(kosdaq_corps)), random_state=99)
    print(f"Sample size: {len(sample)}")
    print()

    results = []
    for i, (_, row) in enumerate(sample.iterrows(), 1):
        corp_code = row["corp_code"]
        corp_name = row["corp_name"]
        stock_code = row["stock_code"]
        has_cfs = False
        fs_type = "unknown"
        row_count = 0

        try:
            df = dart.finstate_all(corp_code, 2022, fs_div="CFS")
            if df is not None and not df.empty:
                row_count = len(df)
                # Check what fs_div values are returned
                if "fs_div" in df.columns:
                    fs_values = df["fs_div"].unique().tolist()
                    if "CFS" in fs_values:
                        has_cfs = True
                        fs_type = "CFS"
                    elif "OFS" in fs_values:
                        fs_type = "OFS_only"
                    else:
                        fs_type = f"other:{fs_values}"
                else:
                    # No fs_div column; presence of data suggests some filing exists
                    has_cfs = True
                    fs_type = "CFS_assumed"
            else:
                fs_type = "no_filing"
        except Exception as e:
            fs_type = f"error"
            print(f"  ERROR for {corp_code}: {e}")

        results.append({
            "corp_code": corp_code,
            "corp_name": corp_name,
            "stock_code": stock_code,
            "has_cfs": has_cfs,
            "fs_type": fs_type,
            "row_count": row_count,
        })
        print(f"[{i:3d}/{len(sample)}] {stock_code} {corp_name[:20]:<20} → {fs_type} ({row_count} rows)")
        time.sleep(SLEEP_BETWEEN)

    df_results = pd.DataFrame(results)
    counts = df_results["fs_type"].value_counts()
    total = len(df_results)

    print()
    print("=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    for fs_type, count in counts.items():
        print(f"  {fs_type:<25} {count:3d}  ({count/total*100:.1f}%)")

    cfs_n = df_results["has_cfs"].sum()
    print()
    print(f"Has CFS:  {cfs_n} ({cfs_n/total*100:.1f}%)")
    print(f"OFS only: {total - cfs_n} ({(total - cfs_n)/total*100:.1f}%)")
    print()

    out_path = RESULTS_DIR / "oq_c_cfs_ofs_split.csv"
    df_results.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
