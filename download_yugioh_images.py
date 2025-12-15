#!/usr/bin/env python3
"""
Yu-Gi-Oh! DB card image downloader (batch)

- Input: cid list file (cids.txt)
- Output: images/<cid>.<ext>   (e.g., images/12424.png)
- Supports:
  - --skip-existing
  - retries/backoff
  - sleep between cids
  - handles Content-Type=application/octet-stream by magic-byte detection

Dependencies:
  pip install requests beautifulsoup4 lxml
"""

import argparse
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.db.yugioh-card.com"


def guess_ext(content_type: str | None) -> str:
    if not content_type:
        return ".jpg"
    ct = content_type.lower().split(";")[0].strip()
    return {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(ct, ".jpg")


def guess_ext_from_bytes(head: bytes) -> str | None:
    if head.startswith(b"\xFF\xD8\xFF"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return ".gif"
    # WEBP: RIFF....WEBP
    if len(head) >= 12 and head[0:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


def read_cids_from_file(path: str) -> list[str]:
    cids: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # allow space-separated tokens per line
            for token in re.split(r"\s+", line):
                if token.isdigit():
                    cids.append(token)
    return cids


def fetch_html(session: requests.Session, url: str, timeout: int, retries: int) -> requests.Response:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    last_err: Exception | None = None
    for i in range(retries + 1):
        try:
            r = session.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last_err = e
            time.sleep(min(2**i, 10))
    assert last_err is not None
    raise last_err


def extract_image_urls(html: str, page_url: str) -> list[tuple[str, str, str]]:
    """
    Returns list of (img_id, title, abs_url)
    Typical: <img id="card_image_1" ... src="/yugiohdb/get_image.action?...">
    """
    soup = BeautifulSoup(html, "lxml")

    imgs = soup.select('img[id^="card_image_"]')
    results: list[tuple[str, str, str]] = []

    for img in imgs:
        src = img.get("src")
        if not src:
            continue
        abs_url = urljoin(page_url, src)
        title = img.get("title") or img.get("alt") or img.get("id") or "card_image"
        img_id = img.get("id") or "card_image"
        results.append((img_id, title, abs_url))

    # Fallback: regex search for get_image.action
    if not results:
        for m in re.finditer(r'(/yugiohdb/get_image\.action\?[^"\']+)', html):
            abs_url = urljoin(page_url, m.group(1))
            results.append(("card_image", "card_image", abs_url))

    # de-duplicate by URL
    uniq: list[tuple[str, str, str]] = []
    seen = set()
    for img_id, title, abs_url in results:
        if abs_url in seen:
            continue
        seen.add(abs_url)
        uniq.append((img_id, title, abs_url))

    return uniq


def download_file(
    session: requests.Session,
    img_url: str,
    referer: str,
    out_tmp_path: str,
    timeout: int,
    retries: int,
) -> str:
    """
    Downloads to out_tmp_path (should end with .tmp),
    determines ext by Content-Type or magic bytes, then renames to final.
    Returns final path.
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": referer,
    }

    os.makedirs(os.path.dirname(out_tmp_path) or ".", exist_ok=True)

    last_err: Exception | None = None
    for i in range(retries + 1):
        try:
            resp = session.get(img_url, headers=headers, stream=True, timeout=timeout)
            resp.raise_for_status()

            ct = (resp.headers.get("Content-Type") or "").lower()

            it = resp.iter_content(chunk_size=1024 * 64)
            first = next(it, b"")
            if not first:
                raise RuntimeError("Empty response body")

            # decide ext
            ext: str | None = None
            if "image/" in ct:
                ext = guess_ext(resp.headers.get("Content-Type"))
            else:
                # Many cases return octet-stream though it's an image
                ext = guess_ext_from_bytes(first[:32])

            if not ext:
                debug_path = out_tmp_path + ".nonimage.bin"
                with open(debug_path, "wb") as f:
                    f.write(first)
                raise RuntimeError(
                    f"Non-image or unknown payload (Content-Type={ct}). "
                    f"Saved head to: {debug_path}"
                )

            # write tmp
            with open(out_tmp_path, "wb") as f:
                f.write(first)
                for chunk in it:
                    if chunk:
                        f.write(chunk)

            # rename to final
            base_path = out_tmp_path[:-4] if out_tmp_path.lower().endswith(".tmp") else out_tmp_path
            final_path = base_path + ext
            os.replace(out_tmp_path, final_path)
            return final_path

        except Exception as e:
            last_err = e
            time.sleep(min(2**i, 10))

    assert last_err is not None
    raise last_err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cid-file", required=True, help="cid一覧ファイル（1行1cid or 空白区切り）")
    ap.add_argument("--locale", default="en", help="request_locale (例: en, ja)")
    ap.add_argument("--outdir", default="images", help="保存先ディレクトリ")
    ap.add_argument("--sleep", type=float, default=0.4, help="cidごとの待機秒（負荷対策）")
    ap.add_argument("--timeout", type=int, default=30, help="HTTPタイムアウト秒")
    ap.add_argument("--retries", type=int, default=2, help="リトライ回数（指数バックオフ）")
    ap.add_argument("--skip-existing", action="store_true", help="images/<cid>.* が存在する場合はスキップ")
    args = ap.parse_args()

    cids = read_cids_from_file(args.cid_file)
    if not cids:
        raise SystemExit("cid が 1件も見つかりませんでした。")

    os.makedirs(args.outdir, exist_ok=True)
    session = requests.Session()

    ok = 0
    ng = 0

    for idx, cid in enumerate(cids, start=1):
        page_url = f"{BASE}/yugiohdb/card_search.action?ope=2&cid={cid}&request_locale={args.locale}"
        print(f"[{idx}/{len(cids)}] cid={cid} page={page_url}")

        try:
            # skip existing (any known ext)
            if args.skip_existing:
                for ext in (".png", ".jpg", ".webp", ".gif"):
                    p = os.path.join(args.outdir, f"{cid}{ext}")
                    if os.path.exists(p):
                        print(f"  - skip existing: {p}")
                        raise StopIteration  # handled below

            page = fetch_html(session, page_url, timeout=args.timeout, retries=args.retries)
            images = extract_image_urls(page.text, page.url)
            if not images:
                raise RuntimeError("画像URLが見つかりませんでした。")

            # 1 cid = first image only
            _, _, img_url = images[0]

            tmp_path = os.path.join(args.outdir, f"{cid}.tmp")
            saved_path = download_file(
                session=session,
                img_url=img_url,
                referer=page.url,
                out_tmp_path=tmp_path,
                timeout=args.timeout,
                retries=args.retries,
            )
            print(f"  - saved: {saved_path}")
            ok += 1

        except StopIteration:
            # skip-existing path
            ok += 1
        except Exception as e:
            ng += 1
            print(f"  !! failed cid={cid}: {e}")

        time.sleep(args.sleep)

    print(f"\nDONE: success={ok}, failed={ng}, total={len(cids)}")


if __name__ == "__main__":
    main()
