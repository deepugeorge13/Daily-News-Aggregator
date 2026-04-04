#!/usr/bin/env python3
"""Run the Bangalore Morning Digest news aggregator."""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import httpx

IST = timezone(timedelta(hours=5, minutes=30))
API_BASE = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")


def get_auth_headers():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return {"x-api-key": key}
    token_file = os.environ.get("CLAUDE_SESSION_INGRESS_TOKEN_FILE")
    if token_file and os.path.exists(token_file):
        token = open(token_file).read().strip()
        return {"Authorization": f"Bearer {token}"}
    raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY environment variable.")


def call_api(payload):
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        **get_auth_headers(),
    }
    resp = httpx.post(
        f"{API_BASE}/v1/messages",
        headers=headers,
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_digest():
    now = datetime.now(IST)
    date_str = now.strftime("%A, %d %B %Y")

    prompt = f"""You are a news aggregator for Bangalore, India. Today is {date_str}, IST.

Using web search, fetch the 3 most important current headlines for each category. Focus on Indian sources: Times of India, The Hindu, Deccan Herald, InShorts, NDTV, Economic Times, MSN India.

Categories:
1. local — Bangalore city news (traffic, civic, local govt, infrastructure, events)
2. national — India national news (central govt, major domestic events, policy)
3. business — Business & Finance (markets, startups, economy, RBI, corporate)
4. tech — Technology (AI, Indian tech, startups, global tech affecting India)
5. intl — International (world events, geopolitics, global economy)

Return ONLY valid JSON, no markdown, no preamble:
{{"local":[{{"source":"Name","headline":"text","summary":"2 sentence summary"}}],"national":[...],"business":[...],"tech":[...],"intl":[...]}}
Each array must have exactly 3 items. Headlines must be factual and from today or last 24 hours."""

    print("Fetching headlines via web search...")
    data = call_api({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 3000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": prompt}],
    })

    raw = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            raw += block["text"]

    m = re.search(r'\{[\s\S]*\}', raw)
    if not m:
        raise ValueError(f"No JSON found in response:\n{raw[:500]}")
    news = json.loads(m.group(0))
    # Strip citation tags from summaries and headlines
    cite_re = re.compile(r'<cite[^>]*>|</cite>')
    for items in news.values():
        for item in items:
            item["headline"] = cite_re.sub("", item.get("headline", "")).strip()
            item["summary"] = cite_re.sub("", item.get("summary", "")).strip()
    return news


def print_digest(news):
    now = datetime.now(IST)
    date_str = now.strftime("%A, %d %B %Y")

    categories = [
        ("local", "Local Bangalore"),
        ("national", "National India"),
        ("business", "Business & Finance"),
        ("tech", "Technology"),
        ("intl", "International"),
    ]

    print()
    print("=" * 60)
    print("  BANGALORE MORNING DIGEST")
    print(f"  {date_str}  ·  {now.strftime('%I:%M %p')} IST")
    print("=" * 60)

    for cat_id, cat_label in categories:
        items = news.get(cat_id, [])
        if not items:
            continue
        print(f"\n{'─' * 60}")
        print(f"  {cat_label.upper()}")
        print(f"{'─' * 60}")
        for i, item in enumerate(items, 1):
            source = item.get("source", "Unknown")
            headline = item.get("headline", "")
            summary = item.get("summary", "")
            print(f"\n{i}. [{source}]")
            print(f"   {headline}")
            print(f"   {summary}")

    print()
    print("=" * 60)
    print("  Powered by Claude + Web Search")
    print("=" * 60)
    print()


def main():
    try:
        news = fetch_digest()
        print_digest(news)

        output_file = "/home/user/Daily-News-Aggregator/digest_output.json"
        with open(output_file, "w") as f:
            json.dump({"date": datetime.now(IST).isoformat(), "news": news}, f, indent=2)
        print(f"Digest saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
