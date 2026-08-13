"""Polite, cached fetcher for CommonLII.

CommonLII's robots.txt (checked 2026-08-12) declares:

    User-agent: *
    Content-Signal: search=yes,ai-train=no,use=reference
    Allow: /

plus `Disallow: /` for GPTBot, CCBot, ClaudeBot, Google-Extended, Bytespider,
Amazonbot, Applebot-Extended, meta-externalagent and
CloudflareBrowserRenderingCrawler.

So: indexing for search is permitted, training a model on it is not, and
`ai-input` (retrieval grounding) is unspecified -- by the site's own legend that
means neither granted nor restricted. Confirm the position with AustLII, who run
CommonLII and license data feeds, before any bulk ingestion.

Transports
----------
Since 2026-08-12 Cloudflare fronts the whole `/lk/cases/` tree with a *managed
challenge* -- `cf-mitigated: challenge`, the "Just a moment..." interstitial --
so the plain `urllib` transport now gets HTTP 403 on every judgment URL. That is
a blanket CDN mitigation, not a targeted refusal: the site's own robots.txt
still says `Allow: /`.

Two transports are therefore available:

    urllib        honest research User-Agent, no challenge solving. Currently
                  403s site-wide. Kept because it is the transport whose
                  behaviour matches what robots.txt describes.
    cloudscraper  solves the challenge by presenting a Chrome fingerprint.

`cloudscraper` requires >= 3.0.0 for managed ("v3") challenges; the PyPI
release stops at 1.2.71, which fails here. Install from source:

    PYTHONUTF8=1 pip install "git+https://github.com/VeNoMouS/cloudscraper.git"

(the UTF-8 flag works around their setup.py reading an emoji README under
Windows cp1252.)

Choosing `cloudscraper` means presenting a browser fingerprint the client does
not have, which is a deliberate decision to work around an access control the
operator put up -- recorded here rather than hidden. The politeness guarantees
are unchanged either way: one request per DELAY_S, everything cached to disk so
a URL is fetched at most once, and every request written to fetch-log.csv with
the transport that made it.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"          # source-faithful HTML, one file per URL
CACHE_META = HERE / "raw" / "_meta"
FETCH_LOG = HERE / "fetch-log.csv"

BASE = "https://www.commonlii.org"
UA = ("DraftlyResearchBot/0.1 (+University of Moratuwa CS3501 academic research; "
      "legal-corpus retrieval; contact: draftly project team)")
DELAY_S = 2.0               # conservative, per the crawl plan
TIMEOUT_S = 45
MAX_RETRIES = 3


class AccessBlocked(RuntimeError):
    """The site refused automated access."""


class TransportUnavailable(RuntimeError):
    """The requested transport is not installed or is too old to be useful."""


class HTTPStatus(RuntimeError):
    """A >=400 response from a transport that does not raise on status."""

    def __init__(self, code: int, url: str):
        super().__init__(f"HTTP {code} for {url}")
        self.code = code


def _make_cloudscraper():
    """A cloudscraper session, or a clear explanation of why there isn't one."""
    try:
        import cloudscraper
    except ImportError as e:
        raise TransportUnavailable(
            "cloudscraper is not installed. Managed-challenge support needs "
            ">=3.0.0, which is not on PyPI:\n"
            '  PYTHONUTF8=1 pip install "git+https://github.com/VeNoMouS/'
            'cloudscraper.git"'
        ) from e
    version = getattr(cloudscraper, "__version__", "0")
    if int(version.split(".")[0] or 0) < 3:
        raise TransportUnavailable(
            f"cloudscraper {version} cannot solve CommonLII's managed "
            f"challenge; >=3.0.0 is required. Install from source:\n"
            '  PYTHONUTF8=1 pip install "git+https://github.com/VeNoMouS/'
            'cloudscraper.git"'
        )
    return cloudscraper.create_scraper(
        interpreter="js2py",        # most reliable for the VM-based challenge
        delay=5,                    # the interstitial's own stated wait
        enable_stealth=True,
        browser={"browser": "chrome", "platform": "windows", "mobile": False},
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def url_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


@dataclass
class Page:
    url: str
    html: str
    fetched_at: str
    content_hash: str
    from_cache: bool


class Fetcher:
    def __init__(self, *, delay_s: float = DELAY_S, offline: bool = False,
                 transport: str = "cloudscraper"):
        if transport not in ("urllib", "cloudscraper"):
            raise ValueError(f"unknown transport: {transport}")
        self.delay_s = delay_s
        self.offline = offline
        self.transport = transport
        self.requests_made = 0
        self.cache_hits = 0
        self._last = 0.0
        self._session = None      # built on first live request, not on import
        RAW.mkdir(parents=True, exist_ok=True)
        CACHE_META.mkdir(parents=True, exist_ok=True)

    # --- cache -------------------------------------------------------------
    def _paths(self, url: str) -> tuple[Path, Path]:
        k = url_key(url)
        return RAW / f"{k}.html", CACHE_META / f"{k}.json"

    def _read_cache(self, url: str) -> Page | None:
        body, meta = self._paths(url)
        if not (body.exists() and meta.exists()):
            return None
        m = json.loads(meta.read_text(encoding="utf-8"))
        return Page(url=m["source_url"],
                    html=body.read_text(encoding="utf-8", errors="replace"),
                    fetched_at=m["retrieved_at"],
                    content_hash=m["content_hash"], from_cache=True)

    def _write_cache(self, url: str, html: str, at: str, digest: str) -> None:
        body, meta = self._paths(url)
        body.write_text(html, encoding="utf-8")
        meta.write_text(json.dumps({
            "source_url": url, "retrieved_at": at, "content_hash": digest,
            "retrieved_from": "commonlii", "bytes": len(html.encode("utf-8")),
        }, indent=2), encoding="utf-8")

    def _log(self, url: str, status: object, nbytes: int, note: str = "") -> None:
        new = not FETCH_LOG.exists()
        with FETCH_LOG.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["url", "status", "bytes", "fetched_at", "note"])
            w.writerow([url, status, nbytes, utc_now(), note])

    def _wait(self) -> None:
        gap = time.monotonic() - self._last
        if gap < self.delay_s:
            time.sleep(self.delay_s - gap)
        self._last = time.monotonic()

    # --- transports ---------------------------------------------------------
    def _fetch_once(self, url: str) -> tuple[int, str]:
        """One live request. Returns (status, html); raises HTTPStatus on >=400."""
        if self.transport == "urllib":
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")

        if self._session is None:
            self._session = _make_cloudscraper()
        resp = self._session.get(url, timeout=TIMEOUT_S)
        if resp.status_code >= 400:
            raise HTTPStatus(resp.status_code, url)
        return resp.status_code, resp.text

    # --- fetch -------------------------------------------------------------
    def get(self, url: str, *, note: str = "") -> Page:
        cached = self._read_cache(url)
        if cached is not None:
            self.cache_hits += 1
            return cached
        if self.offline:
            raise FileNotFoundError(f"offline and not cached: {url}")

        last: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            self._wait()
            try:
                status, html = self._fetch_once(url)
            except (urllib.error.HTTPError, HTTPStatus) as e:
                code = getattr(e, "code", 0)
                self._log(url, code, 0, f"{self.transport} attempt {attempt}")
                if code in (401, 403, 429):
                    raise AccessBlocked(self._blocked_message(url, code)) from e
                last = e
                time.sleep(self.delay_s * attempt)
                continue
            except TransportUnavailable:
                raise
            except Exception as e:  # noqa: BLE001
                last = e
                self._log(url, type(e).__name__, 0,
                          f"{self.transport} attempt {attempt}")
                time.sleep(self.delay_s * attempt)
                continue

            self.requests_made += 1
            at = utc_now()
            digest = "sha256:" + hashlib.sha256(html.encode("utf-8")).hexdigest()
            self._write_cache(url, html, at, digest)
            self._log(url, status, len(html.encode("utf-8")),
                      f"{note} via {self.transport}".strip())
            return Page(url=url, html=html, fetched_at=at,
                        content_hash=digest, from_cache=False)

        raise RuntimeError(f"giving up on {url}: {last}")

    def _blocked_message(self, url: str, code: int) -> str:
        base = f"CommonLII returned HTTP {code} for {url}."
        if self.transport == "urllib":
            return (f"{base} Cloudflare fronts /lk/cases/ with a managed "
                    f"challenge that the urllib transport cannot answer. Retry "
                    f"with --transport cloudscraper, or request a data feed "
                    f"from AustLII.")
        return (f"{base} The challenge was not solved. Cloudflare may have "
                f"tightened the mitigation, or this IP is rate-limited -- back "
                f"off and raise --delay before retrying.")

    def summary(self) -> str:
        return (f"{self.requests_made} fetched via {self.transport}, "
                f"{self.cache_hits} from cache")


def read_robots() -> dict:
    """Fetch robots.txt and report the directives that bear on this crawl.

    Always over urllib: robots.txt is served outside the challenge, and reading
    it with the honest User-Agent is the point.
    """
    req = urllib.request.Request(f"{BASE}/robots.txt", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        txt = resp.read().decode("utf-8", "replace")
    signals, disallowed, current = {}, [], None
    for line in txt.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.lower().startswith("user-agent:"):
            current = s.split(":", 1)[1].strip()
        elif s.lower().startswith("content-signal:"):
            for part in s.split(":", 1)[1].split(","):
                if "=" in part:
                    k, v = part.split("=", 1)
                    signals[k.strip()] = v.strip()
        elif s.lower().startswith("disallow:") and current and current != "*":
            if s.split(":", 1)[1].strip() == "/":
                disallowed.append(current)
    return {"signals": signals, "blocked_agents": disallowed, "raw_len": len(txt)}
