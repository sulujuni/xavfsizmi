"""Tests for the URL scanning engine: default behavior without API keys,
report rendering (including the unknown-domain fix), and the retry helper."""
import httpx
import pytest

import checker


# ─── No API keys configured → safe defaults, no network ──────────────────────

@pytest.mark.asyncio
async def test_virustotal_no_key_returns_default():
    # In the test env no VIRUSTOTAL_API_KEY is set.
    result = await checker.check_virustotal("http://example.com")
    assert result == {"malicious": 0, "total": 0, "found": False}


@pytest.mark.asyncio
async def test_gsb_no_key_returns_safe():
    result = await checker.check_google_safe_browsing("http://example.com")
    assert result == {"dangerous": False}


# ─── Report rendering ────────────────────────────────────────────────────────

def _patch_all(monkeypatch, *, vt, gsb, av, us, age):
    async def _vt(url):
        return vt

    async def _gsb(url):
        return gsb

    async def _av(url):
        return av

    async def _us(url):
        return us

    async def _age(url):
        return age

    monkeypatch.setattr(checker, "check_virustotal", _vt)
    monkeypatch.setattr(checker, "check_google_safe_browsing", _gsb)
    monkeypatch.setattr(checker, "check_alienvault", _av)
    monkeypatch.setattr(checker, "check_urlscan", _us)
    monkeypatch.setattr(checker, "get_domain_age", _age)


@pytest.mark.asyncio
async def test_unknown_domain_age_renders_unknown_and_no_warning(monkeypatch):
    _patch_all(
        monkeypatch,
        vt={"malicious": 0, "total": 70, "found": True},
        gsb={"dangerous": False},
        av={"pulses_count": 0, "dangerous": False},
        us={"verdict": "clean", "score": 0},
        age={"age_days": None, "created": "Noma'lum"},
    )
    report, dangerous = await checker.check_url_complete("http://example.com", "uz")
    assert dangerous is False
    assert "Noma'lum" in report
    # The "new domain" warning must NOT appear when age is unknown.
    assert "juda yangi ochilgan" not in report


@pytest.mark.asyncio
async def test_new_domain_triggers_warning(monkeypatch):
    _patch_all(
        monkeypatch,
        vt={"malicious": 3, "total": 70, "found": True},
        gsb={"dangerous": True},
        av={"pulses_count": 2, "dangerous": True},
        us={"verdict": "malicious", "score": 90},
        age={"age_days": 5, "created": "2026-06-29"},
    )
    report, dangerous = await checker.check_url_complete("http://phish.example", "uz")
    assert dangerous is True
    assert "juda yangi ochilgan" in report


@pytest.mark.asyncio
async def test_check_url_complete_survives_exceptions(monkeypatch):
    async def boom(url):
        raise RuntimeError("network down")

    async def _ok_gsb(url):
        return {"dangerous": False}

    async def _ok_av(url):
        return {"pulses_count": 0, "dangerous": False}

    async def _ok_us(url):
        return {"verdict": "unknown", "score": 0}

    async def _ok_age(url):
        return {"age_days": None, "created": "Noma'lum"}

    monkeypatch.setattr(checker, "check_virustotal", boom)
    monkeypatch.setattr(checker, "check_google_safe_browsing", _ok_gsb)
    monkeypatch.setattr(checker, "check_alienvault", _ok_av)
    monkeypatch.setattr(checker, "check_urlscan", _ok_us)
    monkeypatch.setattr(checker, "get_domain_age", _ok_age)

    # Should not raise even though VirusTotal blew up.
    report, dangerous = await checker.check_url_complete("http://x.example", "uz")
    assert isinstance(report, str)
    assert dangerous is False


# ─── Retry helper ────────────────────────────────────────────────────────────

class _FakeClient:
    """Minimal stand-in for httpx.AsyncClient.request."""

    def __init__(self, behaviors):
        # behaviors: list of either an int status code or an Exception to raise
        self._behaviors = behaviors
        self.calls = 0

    async def request(self, method, url, **kwargs):
        behavior = self._behaviors[self.calls]
        self.calls += 1
        if isinstance(behavior, Exception):
            raise behavior
        return httpx.Response(status_code=behavior, request=httpx.Request(method, url))


@pytest.mark.asyncio
async def test_retry_recovers_after_transient_error(monkeypatch):
    monkeypatch.setattr(checker.asyncio, "sleep", lambda *_a, **_k: _noop())
    client = _FakeClient([httpx.TimeoutException("timeout"), 200])
    resp = await checker._request_with_retry(client, "GET", "http://x")
    assert resp is not None
    assert resp.status_code == 200
    assert client.calls == 2


@pytest.mark.asyncio
async def test_retry_gives_up_and_returns_none(monkeypatch):
    monkeypatch.setattr(checker.asyncio, "sleep", lambda *_a, **_k: _noop())
    client = _FakeClient([httpx.ConnectError("x")] * (checker.MAX_RETRIES + 1))
    resp = await checker._request_with_retry(client, "GET", "http://x")
    assert resp is None


@pytest.mark.asyncio
async def test_retry_on_5xx_status(monkeypatch):
    monkeypatch.setattr(checker.asyncio, "sleep", lambda *_a, **_k: _noop())
    client = _FakeClient([503, 200])
    resp = await checker._request_with_retry(client, "GET", "http://x")
    assert resp.status_code == 200
    assert client.calls == 2


async def _noop():
    return None
