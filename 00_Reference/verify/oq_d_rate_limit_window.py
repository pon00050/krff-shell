"""
OQ-D: Does the DART API rate limit reset per calendar day (00:00 KST),
per rolling 24h, or some other window?

Approach: burst test with 10 calls + scrape DART developer FAQ for any
rate-limit documentation.

Makes exactly 10 DART API calls.
Requires DART_API_KEY in .env.
"""
import sys
import time
import datetime
import requests
from verify_utils import get_dart, RESULTS_DIR

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SAMSUNG_CORP_CODE = "00126380"
BURST_COUNT = 10


def burst_test(dart):
    """Make BURST_COUNT calls in rapid succession and record latency."""
    print(f"Burst test: {BURST_COUNT} calls to dart.company({SAMSUNG_CORP_CODE!r})")
    print()
    observations = []
    for i in range(1, BURST_COUNT + 1):
        t0 = time.perf_counter()
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            result = dart.company(SAMSUNG_CORP_CODE)
            elapsed = time.perf_counter() - t0
            status = "ok" if result is not None else "empty"
        except Exception as e:
            elapsed = time.perf_counter() - t0
            status = f"error: {e}"
        observations.append({"call": i, "timestamp_utc": ts, "elapsed_s": round(elapsed, 3), "status": status})
        print(f"  Call {i:2d}: {elapsed:.3f}s  {status}")

    return observations


def scrape_dart_faq():
    """Attempt to fetch the DART developer FAQ for rate-limit language."""
    url = "https://opendart.fss.or.kr/intro/main.do"
    print(f"\nFetching DART FAQ page: {url}")
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        print(f"  HTTP {resp.status_code}, content-length: {len(resp.content)} bytes")
        text = resp.text

        # Look for rate-limit related Korean/English phrases
        keywords = ["횟수", "하루", "10,000", "10000", "rate", "limit", "quota", "제한", "일일"]
        found_lines = []
        for line in text.splitlines():
            if any(kw in line for kw in keywords):
                stripped = line.strip()
                if stripped and len(stripped) < 300:
                    found_lines.append(stripped)

        if found_lines:
            print("  Rate-limit relevant lines found:")
            for line in found_lines[:20]:
                print(f"    {line}")
        else:
            print("  No rate-limit language found on page (may require JS rendering).")

        return text[:5000], found_lines
    except Exception as e:
        print(f"  Failed to fetch FAQ: {e}")
        return "", []


def main():
    dart = get_dart()
    observations = burst_test(dart)

    faq_snippet, faq_lines = scrape_dart_faq()

    # Write results
    out_path = RESULTS_DIR / "oq_d_rate_limit_observations.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("OQ-D: DART API Rate Limit Window Observations\n")
        f.write("=" * 60 + "\n\n")
        f.write("BURST TEST (10 calls, no sleep between)\n")
        f.write("-" * 40 + "\n")
        for obs in observations:
            f.write(f"  Call {obs['call']:2d} @ {obs['timestamp_utc']}  {obs['elapsed_s']:.3f}s  {obs['status']}\n")

        throttle_seen = any("error" in o["status"] or "020" in o["status"] for o in observations)
        f.write(f"\nThrottling in burst of {BURST_COUNT}: {'YES' if throttle_seen else 'NO'}\n")

        f.write("\nNOTE: Full window reset test cannot be run automatically.\n")
        f.write("It would require monitoring across a day boundary (00:00 KST).\n")
        f.write("Official docs state 10,000 calls/day but do not specify window type.\n")
        f.write("Conservative assumption: calendar-day reset (00:00 KST).\n\n")

        f.write("DART FAQ RATE-LIMIT LINES FOUND\n")
        f.write("-" * 40 + "\n")
        if faq_lines:
            for line in faq_lines:
                f.write(f"  {line}\n")
        else:
            f.write("  (none found — JS-rendered content not accessible via plain requests)\n")

        f.write("\nFAQ PAGE SNIPPET (first 2000 chars)\n")
        f.write("-" * 40 + "\n")
        f.write(faq_snippet[:2000] + "\n")

    print(f"\nWritten: {out_path}")

    throttle_seen = any("error" in o["status"] or "020" in o["status"] for o in observations)
    print(f"\nConclusion: Throttling in burst of {BURST_COUNT}: {'YES' if throttle_seen else 'NO'}")
    print("Full window test not run — requires day-boundary observation.")


if __name__ == "__main__":
    main()
