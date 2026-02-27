"""
OQ-A: Is KSIC Rev.10 Section K (codes 640-669) a complete exclusion set for
financial companies? Does it capture 지주회사 (financial holding companies)
and 리츠 (REITs)?

No API key required.
"""
import sys
import pandas as pd
from verify_utils import RESULTS_DIR

# Fix Windows console encoding for Korean characters
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


KSIC_URL = "https://raw.githubusercontent.com/FinanceData/KSIC/master/KSIC_10.csv.gz"


def main():
    print("Fetching KSIC Rev.10 from GitHub...")
    df = pd.read_csv(KSIC_URL, dtype=str)
    print(f"Loaded {len(df):,} rows. Columns: {list(df.columns)}")
    print()

    # Identify the code column (first column) and name column
    code_col = df.columns[0]
    name_cols = [c for c in df.columns if c != code_col]
    print(f"Code column: {code_col!r}")
    print(f"Name columns: {name_cols}")
    print()

    # Section K: Financial and Insurance Activities — codes 640-669
    section_k = df[df[code_col].str.match(r'^6[4-6]\d', na=False)].copy()
    # Tighten to 640-669 specifically
    def in_range(code):
        try:
            base = int(code[:3])
            return 640 <= base <= 669
        except (ValueError, TypeError):
            return False
    section_k = df[df[code_col].apply(in_range)].copy()

    print(f"Section K (640-669) rows: {len(section_k)}")
    print()
    print(section_k.to_string(index=False))
    print()

    # Search all rows for 지주 and 리츠
    for term in ["지주", "리츠"]:
        matches = df[df.apply(lambda row: any(term in str(v) for v in row), axis=1)]
        print(f"Rows containing '{term}': {len(matches)}")
        if not matches.empty:
            print(matches.to_string(index=False))
        print()

    # Write Section K to CSV
    out_path = RESULTS_DIR / "oq_a_ksic_section_k.csv"
    section_k.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Written: {out_path}")

    # Also write all 지주/리츠 matches
    combined = pd.concat([
        df[df.apply(lambda row: any("지주" in str(v) for v in row), axis=1)].assign(search_term="지주"),
        df[df.apply(lambda row: any("리츠" in str(v) for v in row), axis=1)].assign(search_term="리츠"),
    ]).drop_duplicates()
    out_path2 = RESULTS_DIR / "oq_a_juju_reits_codes.csv"
    combined.to_csv(out_path2, index=False, encoding="utf-8-sig")
    print(f"Written: {out_path2}")


if __name__ == "__main__":
    main()
