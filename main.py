from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from get_definition import get_definition_details
from hanzi_to_pinyin import get_pinyin


app = Flask(__name__)
app.json.ensure_ascii = False


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/pinyin")
def pinyin_endpoint():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text")

    if not isinstance(text, str):
        return jsonify({"error": "请求体必须包含字符串字段 text。"}), 400
    if not text.strip():
        return jsonify({"error": "请输入至少一个汉字或有效字符。"}), 422
    if len(text) > 5000:
        return jsonify({"error": "输入内容不能超过 5000 个字符。"}), 422

    try:
        result = get_pinyin(text)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"text": text, "result": result})


@app.post("/definition")
def definition_endpoint():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text")

    if not isinstance(text, str) or len(text) != 1:
        return jsonify({"error": "请求体必须包含单个字符字段 text。"}), 400

    try:
        definitions, layouts = get_definition_details(text)
    except Exception:
        app.logger.exception("获取汉典释义失败")
        return jsonify({"error": "暂时无法获取释义，请稍后重试。"}), 502

    if not definitions:
        return jsonify({"error": "未找到该字的释义。"}), 404

    return jsonify({"text": text, "definitions": definitions, "layouts": layouts})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
