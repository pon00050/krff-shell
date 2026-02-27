"""
OQ-E: Does `dart_NoncurrentBorrowings` exist as a distinct DART XBRL element
from `dart_LongTermBorrowingsGross`?

Approach: inspect Balance Sheet account_id values for non-current liabilities
across 5 diverse KOSDAQ companies.

Requires DART_API_KEY in .env. ~5 API calls.
"""
import sys
import time
import pandas as pd
from verify_utils import get_dart, RESULTS_DIR

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# 5 diverse KOSDAQ companies: different sectors, mix of large/small
# (corp_code, name, sector_hint)
SAMPLE_CORPS = [
    ("00401731", "셀트리온헬스케어", "pharma"),
    ("00631518", "카카오게임즈", "IT/games"),
    ("00296671", "하나마이크론", "semiconductor"),
    ("00526455", "에코프로비엠", "battery materials"),
    ("00138321", "파라다이스", "leisure/hotel"),
]

TARGET_IDS = {
    "dart_LongTermBorrowingsGross",
    "dart_NoncurrentBorrowings",
    "dart_LongTermDebt",
    "ifrs-full_Borrowings",
    "ifrs_Borrowings",
}

BORROW_KEYWORDS = ["borrow", "debt", "차입", "사채", "장기"]


def main():
    dart = get_dart()
    all_rows = []

    for corp_code, name, sector in SAMPLE_CORPS:
        print(f"Fetching BS for {name} ({corp_code}, {sector})...")
        try:
            df = dart.finstate_all(corp_code, 2022, fs_div="CFS")
            if df is None or df.empty:
                print(f"  Empty response — trying OFS")
                df = dart.finstate_all(corp_code, 2022, fs_div="OFS")

            if df is None or df.empty:
                print(f"  No data available")
                continue

            # Filter to Balance Sheet
            if "sj_div" in df.columns:
                bs = df[df["sj_div"] == "BS"].copy()
            else:
                bs = df.copy()

            # Find non-current liabilities section rows
            # Typically ord 200-299 or account_nm contains "비유동"
            ncl_mask = pd.Series([False] * len(bs), index=bs.index)
            if "account_nm" in bs.columns:
                ncl_mask |= bs["account_nm"].str.contains("비유동", na=False)
                ncl_mask |= bs["account_nm"].str.contains("장기", na=False)
                ncl_mask |= bs["account_nm"].str.contains("사채", na=False)
                ncl_mask |= bs["account_nm"].str.contains("차입", na=False)

            if "account_id" in bs.columns:
                for kw in BORROW_KEYWORDS:
                    ncl_mask |= bs["account_id"].str.lower().str.contains(kw.lower(), na=False)

            ncl_rows = bs[ncl_mask].copy()
            ncl_rows["corp_code"] = corp_code
            ncl_rows["corp_name"] = name
            ncl_rows["sector"] = sector
            all_rows.append(ncl_rows)

            print(f"  BS rows: {len(bs)}, non-current liability rows: {len(ncl_rows)}")

            # Check for target IDs
            if "account_id" in bs.columns:
                found_targets = TARGET_IDS & set(bs["account_id"].dropna())
                if found_targets:
                    print(f"  TARGET IDs found: {found_targets}")
                else:
                    print(f"  None of the target IDs found")

                # Print all unique borrowing-related account_ids
                borrow_ids = bs[bs["account_id"].str.lower().str.contains(
                    "|".join(BORROW_KEYWORDS), na=False, regex=True
                )]["account_id"].unique()
                if len(borrow_ids):
                    print(f"  Borrowing-related account_ids: {list(borrow_ids)}")

        except Exception as e:
            print(f"  ERROR: {e}")

        time.sleep(0.5)

    if not all_rows:
        print("\nNo data collected.")
        return

    combined = pd.concat(all_rows, ignore_index=True)

    print()
    print("=" * 60)
    print("ALL UNIQUE account_id VALUES ACROSS SAMPLES")
    print("=" * 60)
    if "account_id" in combined.columns:
        unique_ids = combined["account_id"].dropna().unique()
        for aid in sorted(unique_ids):
            print(f"  {aid}")
    print()

    print("TARGET ID OCCURRENCE SUMMARY")
    print("-" * 40)
    if "account_id" in combined.columns:
        for tid in sorted(TARGET_IDS):
            count = (combined["account_id"] == tid).sum()
            companies = combined[combined["account_id"] == tid]["corp_name"].unique().tolist()
            print(f"  {tid:<45} found in {count} rows, companies: {companies}")
    print()

    # Save full non-current liability rows
    out_path = RESULTS_DIR / "oq_e_account_ids.csv"
    cols = ["corp_code", "corp_name", "sector", "sj_div", "account_id", "account_nm", "thstrm_amount"]
    save_cols = [c for c in cols if c in combined.columns]
    combined[save_cols].to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
