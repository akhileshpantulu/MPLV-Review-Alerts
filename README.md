# Marriott Review Alerts — Moxy Paris La Villette

Checks marriott.com guest reviews (Bazaarvoice public API, no scraping) every 6 hours via GitHub Actions. When a new review appears, the workflow opens a GitHub Issue containing the full review, and **GitHub emails you the issue automatically** — no SMTP account, no credentials, no extra email address.

## How it works

1. `check_reviews.py` calls the same public Bazaarvoice API endpoint that marriott.com's own reviews page uses (product ID `PARVX`).
2. It compares review IDs against `state.json` (committed in the repo).
3. New reviews produce an alert file; the workflow turns it into a GitHub Issue with date, rating, title, reviewer, and review text. Ratings of 2 or below are flagged LOW SCORE.
4. GitHub notifies you about new issues in your own repos by email (default behavior).
5. The workflow commits the updated `state.json` back so nothing is reported twice. First run sets a baseline and creates no issue.

## Setup (one time, ~5 minutes)

1. Create a new **private** GitHub repository and push these files, keeping the folder structure (`.github/workflows/review-check.yml` must stay at that path).

2. Check your notification settings at https://github.com/settings/notifications — under "Subscriptions > Watching", make sure **Email** is enabled. (You automatically watch repos you create.) Also confirm your email at https://github.com/settings/emails is one you read, e.g. akhilesh.pantulu@highgate.com.

3. Go to the repo's Actions tab, select "Marriott review check", and click **Run workflow** once. This sets the baseline.

4. Done. It runs every 6 hours (UTC). Each new review = one GitHub Issue = one email to you. Close the issue after reading (or don't — it doesn't affect monitoring).

## Notes

- The Bazaarvoice passkey is the public client-side key embedded in marriott.com. If Marriott rotates it, the workflow run fails and GitHub emails you a failure notice; the new key can be read from the network requests on the [hotel's reviews page](https://www.marriott.com/en-us/hotels/parvx-moxy-paris-la-villette/reviews/).
- To monitor another property, change `PRODUCT_ID` in `check_reviews.py` to its Marsha code and delete `state.json`.
- To change frequency, edit the `cron` line in `.github/workflows/review-check.yml`.
- GitHub schedules can drift a few minutes under load; that's normal.
