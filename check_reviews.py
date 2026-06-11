"""Check marriott.com (Bazaarvoice) reviews for Moxy Paris La Villette (PARVX).
Designed to run on a GitHub Actions cron.

When new reviews are found, writes alert.md; the workflow then opens a GitHub
Issue from it, and GitHub emails the repo owner the issue content. No SMTP
credentials needed.

State is kept in state.json in the repo and committed back by the workflow.
First run sets a baseline and creates no alert.
"""

import json
import sys
import urllib.request
from pathlib import Path

PRODUCT_ID = "parvx"
HOTEL_NAME = "Moxy Paris La Villette"
PASSKEY = "canCX9lvC812oa4Y6HYf4gmWK5uszkZCKThrdtYkZqcYE"
API_URL = (
    "https://api.bazaarvoice.com/data/reviews.json"
    f"?apiversion=5.5&passkey={PASSKEY}"
    f"&Filter=ProductId:{PRODUCT_ID}"
    "&Sort=SubmissionTime:desc&Limit=20&Include=Products&Stats=Reviews"
)
STATE_FILE = Path(__file__).parent / "state.json"
ALERT_FILE = Path(__file__).parent / "alert.md"
TITLE_FILE = Path(__file__).parent / "alert_title.txt"


def fetch_reviews():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "review-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("HasErrors"):
        raise RuntimeError(f"Bazaarvoice API error: {data.get('Errors')}")
    return data


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return None


def save_state(reviews):
    state = {
        "lastSeenSubmissionTime": reviews[0]["SubmissionTime"] if reviews else None,
        "lastSeenIds": [r["Id"] for r in reviews],
    }
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def format_review(r):
    rating = r.get("Rating")
    low = " — **LOW SCORE**" if isinstance(rating, int) and rating <= 2 else ""
    text = (r.get("ReviewText") or "").strip()
    if len(text) > 600:
        text = text[:600] + "..."
    secondary = r.get("SecondaryRatings") or {}
    sec = ", ".join(f"{k}: {v['Value']}/5" for k, v in secondary.items() if v and v.get("Value"))
    return (
        f"**Date:** {r.get('SubmissionTime', '')[:10]}\n"
        f"**Rating:** {rating}/5{low}\n"
        f"**Title:** {r.get('Title')}\n"
        f"**Reviewer:** {r.get('UserNickname')}\n"
        + (f"**Category ratings:** {sec}\n" if sec else "")
        + f"\n> {text}\n"
    )


def write_alert(subject, body):
    TITLE_FILE.write_text(subject, encoding="utf-8")
    ALERT_FILE.write_text(body, encoding="utf-8")


def main():
    data = fetch_reviews()
    reviews = data.get("Results", [])
    stats = (
        data.get("Includes", {})
        .get("Products", {})
        .get(PRODUCT_ID.upper(), {})
        .get("ReviewStatistics", {})
    )
    avg = stats.get("AverageOverallRating")
    total = stats.get("TotalReviewCount")

    state = load_state()
    if state is None:
        save_state(reviews)
        print(f"Baseline set: {len(reviews)} reviews recorded. No alert created.")
        return

    seen_ids = set(state.get("lastSeenIds", []))
    new_reviews = [r for r in reviews if r["Id"] not in seen_ids]

    if not new_reviews:
        print(f"No new reviews for {HOTEL_NAME}.")
        save_state(reviews)
        return

    lowest = min(r.get("Rating", 5) for r in new_reviews)
    flag = " [LOW SCORE]" if lowest <= 2 else ""
    date = new_reviews[0].get("SubmissionTime", "")[:10]
    subject = f"{len(new_reviews)} new review(s) at {HOTEL_NAME}{flag} ({date})"
    body = f"New guest review(s) on marriott.com for {HOTEL_NAME}:\n\n"
    body += "\n---\n".join(format_review(r) for r in new_reviews)
    if avg is not None:
        body += f"\n---\n**Current average:** {avg:.2f}/5 across {total} reviews\n"
    body += (
        "\n[View all reviews]"
        "(https://www.marriott.com/en-us/hotels/parvx-moxy-paris-la-villette/reviews/)\n"
    )

    write_alert(subject, body)
    save_state(reviews)
    print(f"Alert written for {len(new_reviews)} new review(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
