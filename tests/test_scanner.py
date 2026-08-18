"""Tests for the URL scanning engine: default behavior without API keys,
report rendering, and the retry helper."""
import httpx
import pytest

from bot.core import scanner


@pytest.mark.asyncio
async def test_virustotal_no_key_returns_default():
    result = await scanner.check_virustotal("http://example.com")
    assert result == {"malicious": 0, "total": 0, "found": False}


@pytest.mark.asyncio
async def test_gsb_no_key_returns_safe():
    result = await scanner.check_google_safe_browsing("http://example.com")
    assert result == {"dangerous": False}


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

    monkeypatch.setattr(scanner, "check_virustotal", _vt)
    monkeypatch.setattr(scanner, "check_google_safe_browsing", _gsb)
    monkeypatch.setattr(scanner, "check_alienvault", _av)
    monkeypatch.setattr(scanner, "check_urlscan", _us)
    monkeypatch.setattr(scanner, "get_domain_age", _age)


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
    report, dangerous = await scanner.check_url_complete("http://example.com", "uz")
    assert dangerous is False
    assert "Noma'lum" in report
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
    report, dangerous = await scanner.check_url_complete("http://phish.example", "uz")
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

    monkeypatch.setattr(scanner, "check_virustotal", boom)
    monkeypatch.setattr(scanner, "check_google_safe_browsing", _ok_gsb)
    monkeypatch.setattr(scanner, "check_alienvault", _ok_av)
    monkeypatch.setattr(scanner, "check_urlscan", _ok_us)
    monkeypatch.setattr(scanner, "get_domain_age", _ok_age)

    report, dangerous = await scanner.check_url_complete("http://x.example", "uz")
    assert isinstance(report, str)
    assert dangerous is False


# ─── Retry helper ────────────────────────────────────────────────────────────

class _FakeClient:
    def __init__(self, behaviors):
        self._behaviors = behaviors
        self.calls = 0

    async def request(self, method, url, **kwargs):
        behavior = self._behaviors[self.calls]
        self.calls += 1
        if isinstance(behavior, Exception):
            raise behavior
        return httpx.Response(status_code=behavior, request=httpx.Request(method, url))


async def _noop():
    return None


@pytest.mark.asyncio
async def test_retry_recovers_after_transient_error(monkeypatch):
    monkeypatch.setattr(scanner.asyncio, "sleep", lambda *_a, **_k: _noop())
    client = _FakeClient([httpx.TimeoutException("timeout"), 200])
    resp = await scanner._request_with_retry(client, "GET", "http://x")
    assert resp is not None
    assert resp.status_code == 200
    assert client.calls == 2


@pytest.mark.asyncio
async def test_retry_gives_up_and_returns_none(monkeypatch):
    monkeypatch.setattr(scanner.asyncio, "sleep", lambda *_a, **_k: _noop())
    client = _FakeClient([httpx.ConnectError("x")] * (scanner.MAX_RETRIES + 1))
    resp = await scanner._request_with_retry(client, "GET", "http://x")
    assert resp is None


@pytest.mark.asyncio
async def test_retry_on_5xx_status(monkeypatch):
    monkeypatch.setattr(scanner.asyncio, "sleep", lambda *_a, **_k: _noop())
    client = _FakeClient([503, 200])
    resp = await scanner._request_with_retry(client, "GET", "http://x")
    assert resp.status_code == 200
    assert client.calls == 2
