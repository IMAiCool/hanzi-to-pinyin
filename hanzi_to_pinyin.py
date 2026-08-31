from __future__ import annotations

from typing import Any

import jieba,re
from pypinyin import Style, pinyin
from get_definition import get_definition



def get_pinyin(text: str) -> list[dict[str, Any]]:
    """先使用 jieba 分词，再逐词生成带声调拼音并还原到每个字符。"""
    result: list[dict[str, Any]] = []
    index = 1

    tex=re.sub(r'[^\u4e00-\u9fff]', '', text)
    
    if len(tex)==1:
        for index,candidates in enumerate(get_definition(tex).keys(),start=1):
            result.append(
                {
                    "index": index, "char": tex, "pinyin": candidates
                }
            )
        return result

    for word in jieba.lcut(text, cut_all=False, HMM=True):
        values = pinyin(
            word,
            style=Style.TONE,
            heteronym=False,
            neutral_tone_with_five=False,
            errors=lambda value: list(value),
        )
        if len(values) != len(word):
            raise ValueError(f"词语 {word!r} 的拼音数量与字符数量不一致")

        for char, candidates in zip(word, values, strict=True):
            result.append(
                {"index": index, "char": char, "pinyin": candidates[0]}
            )
            index += 1

    if len(result) != len(text):
        raise ValueError("转换结果与原文字符数量不一致")
    return result

if __name__=="__main__":
    print(get_pinyin("行"))
