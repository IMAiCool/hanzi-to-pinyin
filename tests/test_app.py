from main import app
from unittest.mock import patch


def test_home():
    client = app.test_client()
    assert client.get("/").status_code == 200


def test_pinyin_api():
    client = app.test_client()
    response = client.post("/pinyin", json={"text": "银行行长！"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["text"] == "银行行长！"
    assert [item["char"] for item in data["result"]] == list("银行行长！")
    assert [item["pinyin"] for item in data["result"][:4]] == ["yín", "háng", "háng", "zhǎng"]


def test_definition_api():
    client = app.test_client()
    result = ({"háng": "行列；排行。"}, {"háng": '<div class="xxjs-reading">释义</div>'})
    with patch("main.get_definition_details", return_value=result):
        response = client.post("/definition", json={"text": "行"})

    assert response.status_code == 200
    assert response.get_json() == {
        "text": "行",
        "definitions": {"háng": "行列；排行。"},
        "layouts": {"háng": '<div class="xxjs-reading">释义</div>'},
    }
