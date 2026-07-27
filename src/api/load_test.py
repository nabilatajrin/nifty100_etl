"""Load test — 10 concurrent screener API calls (Sprint 6, Day 43).

Uses Python threading to fire 10 simultaneous requests at the screener
endpoint and measures response times. Target: all 10 complete within 10s.

Run against a live server:  python -m src.api.load_test
(Or import run_load_test(client) directly for in-process TestClient testing.)
"""

import threading
import time

N_REQUESTS = 10


def _timed_request(fetch_fn, results: list, index: int):
    start = time.time()
    status = fetch_fn()
    elapsed = time.time() - start
    results[index] = (status, elapsed)


def run_load_test(fetch_fn) -> dict:
    """fetch_fn() should perform one request and return the HTTP status code."""
    results = [None] * N_REQUESTS
    threads = []

    overall_start = time.time()
    for i in range(N_REQUESTS):
        t = threading.Thread(target=_timed_request, args=(fetch_fn, results, i))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    overall_elapsed = time.time() - overall_start

    statuses = [r[0] for r in results]
    times = [r[1] for r in results]

    return {
        "n_requests": N_REQUESTS,
        "overall_elapsed_s": round(overall_elapsed, 3),
        "individual_times_s": [round(t, 3) for t in times],
        "max_individual_s": round(max(times), 3),
        "all_within_10s": overall_elapsed < 10.0,
        "all_status_200": all(s == 200 for s in statuses),
        "statuses": statuses,
    }


def main():
    """Standalone run against a live server via requests."""
    import requests

    base_url = "http://localhost:8000/api/v1/screener?min_roe=15"

    def fetch():
        resp = requests.get(base_url, timeout=15)
        return resp.status_code

    result = run_load_test(fetch)
    print(f"10 concurrent screener requests:")
    print(
        f"  Overall elapsed: {result['overall_elapsed_s']}s "
        f"({'PASS' if result['all_within_10s'] else 'FAIL'} — target <10s)"
    )
    print(f"  Max individual request time: {result['max_individual_s']}s")
    print(f"  All returned 200: {result['all_status_200']}")
    print(f"  Individual times: {result['individual_times_s']}")


if __name__ == "__main__":
    main()
