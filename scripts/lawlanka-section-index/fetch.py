"""Polite, cached, resumable HTTP fetcher for the LawLanka structural sweep.

Rules from `statue-plans.md`, all enforced here rather than left to the caller:

- One session, one request per second, sequential. No concurrency.
- Cache to disk keyed by URL. A cached URL is never re-fetched, so the run is
  resumable and idempotent -- re-running the sweep makes zero requests.
- The account is a single seat with concurrent-session limiting. If the site
  answers with the "close last session" confirm, abort loudly instead of
  closing someone else's session.
- Credentials come from `.env` only.

Every response carries provenance: `source_url`, `fetched_at`, `sha256`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

import config as C


class SessionConflict(RuntimeError):
    """The single seat is in use elsewhere; a human must sort it out."""


class NotLoggedIn(RuntimeError):
    """The response is the login page, so the session is not authenticated."""


# Text the site shows when the one seat is already in use.
CONFLICT_RE = re.compile(
    r"close\s+(?:the\s+)?last\s+session|already\s+logged\s+in|"
    r"access\s+from\s+this\s+system", re.I)
LOGIN_PAGE_RE = re.compile(
    r"userMaster\.(?:emailAddress|password)|name=[\"']?logInDirect", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cache_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


@dataclass
class Page:
    url: str
    html: str
    fetched_at: str
    sha256: str
    from_cache: bool

    @property
    def provenance(self) -> dict:
        return {"source_url": self.url, "fetched_at": self.fetched_at,
                "sha256": self.sha256, "retrieved_from": C.RETRIEVED_FROM}


class Fetcher:
    def __init__(self, *, delay_s: float = C.DELAY_S, offline: bool = False):
        self.delay_s = delay_s
        self.offline = offline          # cache-only; never touch the network
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": C.UA})
        self.logged_in = False
        self.requests_made = 0
        self.cache_hits = 0
        self._last_request_at = 0.0

    # --- cache ---------------------------------------------------------------
    def _paths(self, url: str) -> tuple[Path, Path]:
        k = cache_key(url)
        return C.CACHE / f"{k}.html", C.CACHE / f"{k}.meta.json"

    def _read_cache(self, url: str) -> Page | None:
        body, meta = self._paths(url)
        if not (body.exists() and meta.exists()):
            return None
        m = json.loads(meta.read_text(encoding="utf-8"))
        return Page(url=m["source_url"], html=body.read_text(encoding="utf-8",
                                                             errors="replace"),
                    fetched_at=m["fetched_at"], sha256=m["sha256"],
                    from_cache=True)

    def _write_cache(self, url: str, html: str, fetched_at: str, digest: str) -> None:
        body, meta = self._paths(url)
        body.write_text(html, encoding="utf-8")
        meta.write_text(json.dumps(
            {"source_url": url, "fetched_at": fetched_at, "sha256": digest,
             "retrieved_from": C.RETRIEVED_FROM, "bytes": len(html.encode("utf-8"))},
            indent=2), encoding="utf-8")

    # --- log -----------------------------------------------------------------
    def _log(self, url: str, status: object, nbytes: int, fetched_at: str,
             note: str = "") -> None:
        new = not C.FETCH_LOG.exists()
        with C.FETCH_LOG.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["url", "status", "bytes", "fetched_at", "note"])
            w.writerow([url, status, nbytes, fetched_at, note])

    # --- politeness ----------------------------------------------------------
    def _wait(self) -> None:
        gap = time.monotonic() - self._last_request_at
        if gap < self.delay_s:
            time.sleep(self.delay_s - gap)
        self._last_request_at = time.monotonic()

    # --- auth ----------------------------------------------------------------
    def login(self) -> None:
        if self.logged_in:
            return
        if self.offline:
            raise NotLoggedIn("offline mode: cannot log in")
        if not (C.LAWLANKA_USER and C.LAWLANKA_PASS):
            raise NotLoggedIn(
                "LAWLANKA_USER / LAWLANKA_PASS are not in .env. Rotate the "
                "password first (the old one was pasted into a chat log), then "
                "add both keys. Never put them in a script or a notebook.")
        user_field, pass_field, direct_field, name_field = C.LOGIN_FIELDS
        payload = {user_field: C.LAWLANKA_USER, pass_field: C.LAWLANKA_PASS,
                   direct_field: "true", name_field: ""}
        self._wait()
        r = self.session.post(C.LOGIN_URL, data=payload, timeout=C.TIMEOUT_S,
                              allow_redirects=True)
        self.requests_made += 1
        self._log(C.LOGIN_URL, r.status_code, len(r.content), utc_now(), "login")
        if CONFLICT_RE.search(r.text):
            raise SessionConflict(
                "LawLanka is reporting an existing session on this account. Do "
                "not run the scraper while a person is logged in -- confirm the "
                "seat is free, then retry.")
        if r.status_code != 200:
            raise NotLoggedIn(f"login returned HTTP {r.status_code}")
        if LOGIN_PAGE_RE.search(r.text):
            raise NotLoggedIn(
                "login POST returned the login form again -- credentials "
                "rejected, or the form fields have changed.")
        self.logged_in = True

    # --- fetch ---------------------------------------------------------------
    def get(self, url: str, *, note: str = "") -> Page:
        cached = self._read_cache(url)
        if cached is not None:
            self.cache_hits += 1
            return cached
        if self.offline:
            raise FileNotFoundError(f"offline mode and not cached: {url}")
        if not self.logged_in:
            self.login()

        last_err: Exception | None = None
        for attempt in range(1, C.MAX_RETRIES + 1):
            self._wait()
            try:
                r = self.session.get(url, timeout=C.TIMEOUT_S)
            except requests.RequestException as e:
                last_err = e
                self._log(url, f"error:{type(e).__name__}", 0, utc_now(),
                          f"attempt {attempt}")
                time.sleep(self.delay_s * attempt)
                continue
            self.requests_made += 1
            fetched_at = utc_now()
            if CONFLICT_RE.search(r.text):
                self._log(url, r.status_code, len(r.content), fetched_at,
                          "session-conflict")
                raise SessionConflict(
                    f"session conflict while fetching {url} -- another login is "
                    f"active on the single seat. Stopping.")
            if r.status_code != 200:
                self._log(url, r.status_code, len(r.content), fetched_at,
                          f"attempt {attempt}")
                last_err = RuntimeError(f"HTTP {r.status_code} for {url}")
                time.sleep(self.delay_s * attempt)
                continue
            if LOGIN_PAGE_RE.search(r.text):
                # session expired mid-run: log in once and retry this URL
                self._log(url, r.status_code, len(r.content), fetched_at,
                          "session-expired")
                self.logged_in = False
                self.login()
                continue
            digest = hashlib.sha256(r.content).hexdigest()
            self._write_cache(url, r.text, fetched_at, digest)
            self._log(url, r.status_code, len(r.content), fetched_at, note)
            return Page(url=url, html=r.text, fetched_at=fetched_at,
                        sha256=digest, from_cache=False)

        raise RuntimeError(f"giving up on {url} after {C.MAX_RETRIES} attempts: "
                           f"{last_err}")

    # --- reporting -----------------------------------------------------------
    def summary(self) -> str:
        return (f"{self.requests_made} request(s) made, "
                f"{self.cache_hits} served from cache")


def preflight() -> list[str]:
    """Report every reason the network run must not start yet."""
    blockers = []
    if not C.LAWLANKA_USER:
        blockers.append("LAWLANKA_USER missing from .env")
    if not C.LAWLANKA_PASS:
        blockers.append("LAWLANKA_PASS missing from .env")
    return blockers
