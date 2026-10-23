"""Publish one Markdown source without rewriting the article. Secrets come from env only."""
import argparse, json, os, sys, urllib.request, urllib.error, urllib.parse
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "publish-state.json"

def request(url, method="GET", payload=None, headers=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Content-Type": "application/json", "User-Agent": "CableFam-publisher/1.0", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # Never log token-bearing request bodies or provider response bodies.
        raise RuntimeError(f"API request failed: HTTP {error.code}") from None

def secret(name):
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Missing secret: {name}")
    return value

def save(state):
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=["dev", "blogger"])
    parser.add_argument("--create", action="store_true", help="Explicit first-time creation only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    source = (ROOT / "article.md").read_text(encoding="utf-8")
    if not source.startswith("# "):
        raise RuntimeError("Source must begin with an H1 title")
    title = source.splitlines()[0][2:]
    config = json.loads((ROOT / "publish-config.json").read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    target = state.get(args.platform, {})
    html = markdown.markdown(source, extensions=["tables", "fenced_code"])
    if args.dry_run:
        print(json.dumps({"platform": args.platform, "title": title,
            "source_characters": len(source), "tables": html.count("<table>"),
            "official_link": 'href="https://cablefam.com/"' in html,
            "mode": "update" if target.get("id") else "creation requires --create"}))
        return
    if not target.get("id") and not args.create:
        raise RuntimeError("No saved article ID. Run once with --create; updates never create replacements.")
    if args.platform == "dev":
        headers = {"api-key": secret("DEV_API_KEY"), "Accept": "application/vnd.forem.api-v1+json"}
        payload = {"article": {"title": title, "body_markdown": source, "published": True}}
        url = "https://dev.to/api/articles"
        if target.get("id"):
            url += "/" + str(int(target["id"]))
        result = request(url, "PUT" if target.get("id") else "POST", payload, headers)
    else:
        form = urllib.parse.urlencode({"client_id": secret("BLOGGER_CLIENT_ID"),
            "client_secret": secret("BLOGGER_CLIENT_SECRET"),
            "refresh_token": secret("BLOGGER_REFRESH_TOKEN"),
            "grant_type": "refresh_token"}).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=form)
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                token = json.load(response)["access_token"]
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Google OAuth failed: HTTP {error.code}") from None
        headers = {"Authorization": "Bearer " + token}
        blog_id = str(config["blogger_blog_id"])
        if not blog_id.isdigit():
            raise RuntimeError("Invalid Blogger blog ID")
        url = "https://www.googleapis.com/blogger/v3/blogs/" + blog_id + "/posts"
        if target.get("id"):
            url += "/" + str(int(target["id"]))
        result = request(url, "PUT" if target.get("id") else "POST",
            {"kind": "blogger#post", "title": title, "content": html}, headers)
    state[args.platform] = {"id": str(result["id"]), "url": result["url"]}
    save(state)
    print(json.dumps(state[args.platform]))

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
