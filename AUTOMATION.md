# Profile maintenance

The profile refreshes daily at **04:23 UTC**, or manually from **Actions → Refresh profile → Run workflow**. Scheduling is best-effort and can be delayed by GitHub. GitHub may disable public schedules after 60 days without repository activity; re-enable the workflow in Actions if necessary.

## What changes

- Public repository count, stars (including forks), and follower count.
- Languages measured by bytes in public non-fork projects. This profile repository is excluded so its generator code doesn't skew the result.
- Up to three recent public events/releases from non-fork projects, excluding this profile repository. No private repositories or credentials are published.
- Timestamp, SVG images, and accessible image descriptions.

The banner and featured project remain intentionally curated. Color tokens live in `palette.json`. Public API data is fetched by GitHub CLI using the workflow's temporary `GITHUB_TOKEN`, not a personal token. Python uses only its standard library. Validation runs before any generated change is committed.

## Cost check — November 1, 2026

This workflow uses a **standard `ubuntu-latest` runner in a public repository**. GitHub currently documents this compute as free; it does not consume the private-repository included compute allowance. It uploads **no Actions artifacts**, creates **no caches or packages**, and uses **no larger runners, paid services, or external widget hosting**. Generated images are small ordinary repository files.

Official references:
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/concepts/billing-and-usage
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

Changing the repository to private, selecting paid runners, adding paid services/storage, or future GitHub policy changes can change this assessment.
