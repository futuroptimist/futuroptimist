import os
import requests
import datetime as dt
import pandas as pd
import calplot
from pathlib import Path

API_URL = "https://api.github.com/graphql"
LOGIN = "futuroptimist"
OWNERS = {"futuroptimist", "democratizedspace"}
OUTPUT_PATH = Path("assets/pr_heatmap.svg")

QUERY = """
query($login:String!, $after:String, $from:DateTime!, $to:DateTime!) {
  user(login:$login){
    contributionsCollection(from:$from, to:$to){
      pullRequestContributions(first:100, after:$after) {
        edges {
          node {
            occurredAt
            pullRequest { repository { owner { login } } }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""


def fetch_pr_dates(year: int) -> list[str]:
    token = os.environ["GH_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}
    from_ts = f"{year}-01-01T00:00:00Z"
    to_ts = f"{year}-12-31T23:59:59Z"
    after = None
    dates: list[str] = []
    while True:
        variables = {"login": LOGIN, "after": after, "from": from_ts, "to": to_ts}
        resp = requests.post(
            API_URL,
            json={"query": QUERY, "variables": variables},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        contribs = data["data"]["user"]["contributionsCollection"][
            "pullRequestContributions"
        ]
        for edge in contribs.get("edges", []):
            node = edge["node"]
            owner = node["pullRequest"]["repository"]["owner"]["login"]
            if owner in OWNERS:
                dates.append(node["occurredAt"][:10])
        if not contribs["pageInfo"]["hasNextPage"]:
            break
        after = contribs["pageInfo"]["endCursor"]
    return dates


def generate_heatmap(dates: list[str], year: int, output: Path = OUTPUT_PATH) -> None:
    if dates:
        series = pd.Series(1, index=pd.to_datetime(dates))
        series = series.resample("D").sum()
    else:
        series = pd.Series(dtype=int)
        series = series.reindex(pd.date_range(f"{year}-01-01", f"{year}-12-31"))
        series[:] = 0
    series = series.reindex(
        pd.date_range(f"{year}-01-01", f"{year}-12-31"), fill_value=0
    )
    ax = calplot.yearplot(series, year=year, cmap="Greens", linewidth=0.5)
    fig = ax.get_figure()
    fig.set_size_inches(8, 2)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", transparent=True)


def main() -> None:
    year = dt.date.today().year
    dates = fetch_pr_dates(year)
    generate_heatmap(dates, year)


if __name__ == "__main__":
    main()
