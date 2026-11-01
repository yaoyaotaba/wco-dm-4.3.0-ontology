import json
import ssl
import time
import urllib.error
import urllib.request

TOKEN = open("../../.gh_token").read().strip()
REPO = "yaoyaotaba/wco-dm-4.3.0-ontology"
CTX = ssl._create_unverified_context()


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        "https://api.github.com" + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "pages-setup",
        },
    )
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=40) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


status, pages = api("GET", f"/repos/{REPO}/pages")
print("GET pages:", status)
if status == 404:
    status, pages = api(
        "POST",
        f"/repos/{REPO}/pages",
        {"source": {"branch": "main", "path": "/"}},
    )
    print("POST pages:", status, json.dumps(pages)[:300])
else:
    status, pages = api(
        "PUT",
        f"/repos/{REPO}/pages",
        {"source": {"branch": "main", "path": "/"}},
    )
    print("PUT pages:", status, json.dumps(pages)[:300])

for attempt in range(40):
    status, build = api("GET", f"/repos/{REPO}/pages/builds/latest")
    state = build.get("status") if isinstance(build, dict) else None
    print(f"build {attempt}: {status} {state} {build.get('error', {}).get('message', '') if isinstance(build, dict) else ''}")
    if state in ("built", "errored"):
        break
    time.sleep(10)

status, info = api("GET", f"/repos/{REPO}/pages")
print("final pages:", status, json.dumps({k: info.get(k) for k in ("html_url", "status", "cname", "http", "build_type") if isinstance(info, dict)}))