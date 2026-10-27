"""Update mapped WordPress.com posts; never create fallback duplicates."""
import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
API = "https://public-api.wordpress.com/rest/v1.1"

class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
    def handle_data(self, data):
        self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs).get("href"))
    def normalized(self):
        return " ".join(" ".join(self.parts).split())

def inspect(content):
    parser = Visible()
    parser.feed(content)
    return parser

def blocks(rendered):
    pattern = re.compile(r"<(h[1-6]|p|table)\b[^>]*>[\s\S]*?</\1>")
    parts = []
    end = 0
    for match in pattern.finditer(rendered):
        if rendered[end:match.start()].strip():
            raise RuntimeError("Unsupported Markdown block; nothing published")
        tag, element = match.group(1), match.group()
        if tag.startswith("h"):
            level = int(tag[1])
            element = element.replace("<" + tag + ">", '<' + tag + ' class="wp-block-heading">', 1)
            parts.append('<!-- wp:heading ' + json.dumps({"level":level}) + ' -->\n' + element + '\n<!-- /wp:heading -->')
        elif tag == "table":
            parts.append('<!-- wp:table {"hasFixedLayout":false} -->\n<figure class="wp-block-table">' + element + '</figure>\n<!-- /wp:table -->')
        else:
            parts.append('<!-- wp:paragraph -->\n' + element + '\n<!-- /wp:paragraph -->')
        end = match.end()
    if rendered[end:].strip() or not parts:
        raise RuntimeError("Unsupported or empty article; nothing published")
    result = "\n\n".join(parts)
    if inspect(rendered).normalized() != inspect(result).normalized():
        raise RuntimeError("Conversion changed article text")
    return result

def request(site, post, token, payload=None):
    url = f"{API}/sites/{site}/posts/{post}/?context=edit"
    req = urllib.request.Request(url,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        method="GET" if payload is None else "POST",
        headers={"Authorization":"Bearer " + token, "Content-Type":"application/json",
                 "User-Agent":"CableFam-WordPress-sync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Provider bodies/headers may contain credentials; never log them.
        raise RuntimeError(f"WordPress API returned HTTP {exc.code}; no fallback creation") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("WordPress API unavailable; rerun after recovery") from None

def validate_target(result, site, article):
    if (int(result.get("ID", 0)) != article["post_id"]
            or int(result.get("site_ID", 0)) != site
            or result.get("URL") != article["url"]
            or result.get("status") != "publish"):
        raise RuntimeError("Target ID, site, URL or published status mismatch")

def prepare(config):
    site = config["site_id"]
    if type(site) is not int or site <= 0 or not config["articles"]:
        raise RuntimeError("Invalid site/mapping")
    prepared, targets = [], set()
    for article in config["articles"]:
        post = article["post_id"]
        if type(post) is not int or post <= 0 or post in targets:
            raise RuntimeError("Missing or duplicate post ID; create/map new posts separately")
        targets.add(post)
        path = (ROOT / article["source"]).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            raise RuntimeError("Source escapes repository")
        source = path.read_text(encoding="utf-8")
        if not source.startswith("# "):
            raise RuntimeError("Source must start with an H1")
        rendered = markdown.markdown(source, extensions=["tables", "fenced_code"])
        if "https://cablefam.com/" not in inspect(rendered).links:
            raise RuntimeError("Official CableFam hyperlink missing")
        content = blocks(rendered)
        prepared.append((article, {
            "title":source.splitlines()[0][2:], "content":content, "publicize":False
        }))
    return site, prepared

def run(dry_run=False):
    config = json.loads((ROOT / "wordpress-sync.json").read_text(encoding="utf-8"))
    site, prepared = prepare(config)
    if dry_run:
        for article, payload in prepared:
            print(json.dumps({"mode":"dry-run", "source":article["source"],
                "site_id":site, "post_id":article["post_id"],
                "tables":payload["content"].count("<table>"),
                "heading_blocks":payload["content"].count("<!-- wp:heading"),
                "official_link":True}, ensure_ascii=False))
        return
    token = os.environ.get("WORDPRESS_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing WORDPRESS_ACCESS_TOKEN; nothing published")
    # Check all destinations before writing any article.
    for article, _ in prepared:
        validate_target(request(site, article["post_id"], token), site, article)
    for article, payload in prepared:
        result = request(site, article["post_id"], token, payload)
        validate_target(result, site, article)
        saved = request(site, article["post_id"], token)
        validate_target(saved, site, article)
        actual, expected = inspect(saved.get("content", "")), inspect(payload["content"])
        if actual.normalized() != expected.normalized() or actual.links != expected.links:
            raise RuntimeError("Saved content/link verification failed; inspect existing post")
        if saved["content"].count("<table") != payload["content"].count("<table"):
            raise RuntimeError("Saved table verification failed")
        print(json.dumps({"mode":"updated","post_id":article["post_id"],
            "url":article["url"],"modified":saved.get("modified")}, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    try:
        run(parser.parse_args().dry_run)
    except (RuntimeError, KeyError, ValueError, OSError) as exc:
        # Only controlled messages; do not print token-bearing request objects.
        print("WordPress sync failed: " + str(exc), file=sys.stderr)
        sys.exit(1)
