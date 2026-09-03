from app import app


def test_health():
    client = app.test_client()
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_learn_page_renders():
    client = app.test_client()
    res = client.get("/learn")
    assert res.status_code == 200
    assert b"five small steps" in res.data
