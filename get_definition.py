"""获取汉典中指定汉字或词语的详细解释。"""

from __future__ import annotations

import json
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


BASE_URL = "https://www.zdic.net/hans/{text}"
REQUEST_TIMEOUT = 10
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"
    )
}
SAFE_LAYOUT_CLASSES = {"encs", "sym", "dichr"}


def _parse_definition(html: bytes | str) -> dict[str, str]:
    """按拼音节点将 ``section#xxjs`` 中的文本划分为多个释义。"""
    soup = BeautifulSoup(html, "html.parser")
    section = soup.select_one("section#xxjs")
    if section is None:
        return {}

    marker_classes = {"xxjs-pos__py", "xxjs-reading__py"}
    definitions: dict[str, list[str]] = {}
    current_key: str | None = None

    for node in section.descendants:
        if (
            isinstance(node, Tag)
            and node.name == "span"
            and marker_classes.intersection(node.get("class", []))
        ):
            current_key = node.get_text(" ", strip=True)
            if current_key:
                definitions.setdefault(current_key, [])
            continue

        if not isinstance(node, NavigableString) or not current_key:
            continue
        if any(
            parent.name == "span"
            and marker_classes.intersection(parent.get("class", []))
            for parent in node.parents
        ):
            continue

        value = " ".join(str(node).split())
        if value:
            definitions[current_key].append(value)

    return {
        key: "\n".join(values)
        for key, values in definitions.items()
    }


def _parse_definition_layout(html: bytes | str) -> dict[str, str]:
    """提取按读音分组的原始语义结构，并移除可执行或交互内容。"""
    soup = BeautifulSoup(html, "html.parser")
    section = soup.select_one("section#xxjs")
    if section is None:
        return {}

    layouts: dict[str, str] = {}
    for reading in section.select("div.xxjs-reading"):
        pinyin = reading.select_one(".xxjs-reading__py")
        if pinyin is None:
            continue

        fragment = BeautifulSoup(str(reading), "html.parser")
        for unsafe in fragment.select("script, style, iframe, form, button, svg, audio, video"):
            unsafe.decompose()
        for link in fragment.find_all("a"):
            if "xxjs-cizu__word" in link.get("class", []):
                if link.find_next_sibling("a", class_="xxjs-cizu__word") is not None:
                    link.insert_after("、")
                link.name = "span"
            else:
                link.unwrap()
        for tag in fragment.find_all(True):
            classes = [
                value for value in tag.get("class", [])
                if value.startswith("xxjs-") or value in SAFE_LAYOUT_CLASSES
            ]
            tag.attrs.clear()
            if classes:
                tag["class"] = classes

        key = pinyin.get_text(" ", strip=True)
        value = str(fragment.div) if fragment.div else ""
        if key and value:
            layouts[key] = layouts.get(key, "") + value
    return layouts


def _request_definition_page(text: str) -> bytes:
    url = BASE_URL.format(text=quote(text.strip(), safe=""))
    response = requests.get(
        url,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.content


def get_definition(text: str) -> dict[str, str]:
    """返回以读音为键、对应释义为值的 JSON 可序列化字典。"""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text 必须是非空字符串")

    return _parse_definition(_request_definition_page(text))


def get_definition_details(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """一次请求同时返回纯文本释义和保留原层级的安全 HTML。"""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text 必须是非空字符串")

    html = _request_definition_page(text)
    return _parse_definition(html), _parse_definition_layout(html)


if __name__ == "__main__":
    print(json.dumps(get_definition("重"), ensure_ascii=False, indent=2))
