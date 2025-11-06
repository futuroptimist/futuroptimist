import sys

from tools.youtube_mcp import __main__


def test_main_runs_uvicorn(monkeypatch):
    called = {}

    def fake_run(app, host=None, port=None, reload=None):
        called["host"] = host
        called["port"] = port
        called["app"] = app

    monkeypatch.setattr(__main__.uvicorn, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["ytmcp", "--host", "0.0.0.0", "--port", "9999"])

    __main__.main()
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 9999
    assert called["app"] == "tools.youtube_mcp.http_server:app"
