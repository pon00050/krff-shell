"""
OQ-F: Does the DART bulk download (fnltt/dwld/main.do) require login/API key?
What is the file format and column structure?

No API key required for initial probe.
"""
import sys
import io
import requests
from bs4 import BeautifulSoup
from verify_utils import RESULTS_DIR

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


MAIN_URL = "https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://opendart.fss.or.kr/",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}

findings = []


def log(msg):
    print(msg)
    findings.append(msg)


def probe_main_page():
    log(f"Probing: {MAIN_URL}")
    try:
        resp = requests.get(MAIN_URL, headers=HEADERS, timeout=20)
        log(f"  HTTP {resp.status_code}")
        log(f"  Content-Type: {resp.headers.get('Content-Type', 'unknown')}")
        log(f"  Content-Length: {len(resp.content)} bytes")

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            log("  → HTML response (likely page, not direct download)")
            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for download links
            links = soup.find_all("a", href=True)
            download_links = [a for a in links if any(
                kw in a["href"].lower() for kw in ["download", "dwld", ".zip", ".txt", ".csv"]
            )]
            log(f"  Download links found: {len(download_links)}")
            for a in download_links[:10]:
                log(f"    {a.get('href')} — {a.get_text(strip=True)[:80]}")

            # Look for forms (POST endpoints)
            forms = soup.find_all("form")
            log(f"  Forms found: {len(forms)}")
            for form in forms:
                log(f"    action={form.get('action')} method={form.get('method')}")
                inputs = form.find_all("input")
                for inp in inputs[:10]:
                    log(f"      input: name={inp.get('name')} value={inp.get('value')} type={inp.get('type')}")

            # Look for login indicators
            login_keywords = ["login", "로그인", "sign in", "인증", "아이디", "비밀번호"]
            page_lower = resp.text.lower()
            is_login_wall = any(kw in page_lower for kw in login_keywords)
            log(f"  Login wall detected: {is_login_wall}")

            # Return first 3000 chars of HTML for inspection
            return resp.text[:3000]

        elif "application" in content_type:
            log("  → Direct file download response")
            # Try to read as tab-delimited cp949
            try:
                text = resp.content.decode("cp949")
                lines = text.splitlines()
                log(f"  Lines: {len(lines)}")
                log(f"  First line (columns): {lines[0] if lines else 'empty'}")
                for line in lines[1:6]:
                    log(f"  Sample row: {line[:200]}")
            except Exception as e:
                log(f"  Could not decode as cp949: {e}")
            return None

    except Exception as e:
        log(f"  ERROR: {e}")
        return None


def try_direct_download_urls():
    """Try common patterns for DART bulk download URLs."""
    log("\nTrying known DART bulk download URL patterns...")

    candidate_urls = [
        # Pattern observed in some DART documentation
        "https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/downloadFnltt.do?fnlttYear=2022&fnlttQe=11",
        "https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do?fnlttYear=2022&fnlttQe=11",
    ]

    for url in candidate_urls:
        log(f"  Trying: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
            log(f"    HTTP {resp.status_code}, Content-Type: {resp.headers.get('Content-Type', '?')}, Size: {len(resp.content)} bytes")
            if resp.status_code == 200 and len(resp.content) > 1000:
                ct = resp.headers.get("Content-Type", "")
                if "text" in ct and "html" not in ct:
                    # Might be actual data
                    try:
                        text = resp.content.decode("cp949")
                        lines = text.splitlines()
                        log(f"    Columns: {lines[0][:300] if lines else 'empty'}")
                        for line in lines[1:4]:
                            log(f"    Row: {line[:200]}")
                    except Exception as e:
                        log(f"    Decode error: {e}")
        except Exception as e:
            log(f"    ERROR: {e}")


def main():
    html_snippet = probe_main_page()
    try_direct_download_urls()

    out_path = RESULTS_DIR / "oq_f_bulk_download_findings.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("OQ-F: DART Bulk Download Access Probe\n")
        f.write("=" * 60 + "\n\n")
        for line in findings:
            f.write(line + "\n")

        if html_snippet:
            f.write("\n" + "=" * 60 + "\n")
            f.write("HTML PAGE SNIPPET (first 3000 chars)\n")
            f.write("=" * 60 + "\n")
            f.write(html_snippet)

    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
