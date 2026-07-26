#!/usr/bin/env python3
"""Update the embedded elementary-kanji data to the 2017 curriculum."""
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ADD = {
    "茨": ("シ・ジ", "いばら", "茨城（いばらき）"), "媛": ("エン", "ひめ", "愛媛（えひめ）"),
    "岡": ("コウ", "おか", "岡山（おかやま）"), "潟": ("セキ", "かた・-がた", "新潟（にいがた）"),
    "岐": ("キ・ギ", "なし", "岐阜（ぎふ）"), "熊": ("ユウ", "くま", "熊本（くまもと）"),
    "香": ("コウ・キョウ", "か・かお-り", "香川（かがわ）"), "佐": ("サ", "なし", "佐賀（さが）"),
    "埼": ("キ", "さき", "埼玉（さいたま）"), "崎": ("キ", "さき", "長崎（ながさき）"),
    "滋": ("ジ・シ", "なし", "滋賀（しが）"), "鹿": ("ロク", "しか・か", "鹿児島（かごしま）"),
    "縄": ("ジョウ", "なわ", "沖縄（おきなわ）"), "井": ("セイ・ショウ", "い", "井戸（いど）"),
    "沖": ("チュウ", "おき", "沖縄（おきなわ）"), "栃": ("なし", "とち", "栃木（とちぎ）"),
    "奈": ("ナ", "なし", "奈良（なら）"), "梨": ("リ", "なし", "梨（なし）"),
    "阪": ("ハン", "さか", "大阪（おおさか）"), "阜": ("フ・フウ", "なし", "岐阜（ぎふ）"),
}
MOVES = {4: "賀群徳富城"}
TO5 = "囲紀喜救型航告殺士史象賞貯停堂得毒費粉脈歴"
TO6 = "胃腸恩券承舌銭退敵俵預"

def block(text, start, end):
    m = re.search(start + r"([\s\S]*?)" + end, text)
    if not m: raise ValueError(start)
    return m, m.group(1)

def paths(svg_dir, char):
    root = ET.parse(svg_dir / f"{ord(char):05x}.svg").getroot()
    return [e.attrib['d'] for e in root.iter() if e.tag.endswith('path') and 'd' in e.attrib]

def main():
    app, svg_dir = Path(sys.argv[1]), Path(sys.argv[2])
    text = app.read_text()
    dm, data_text = block(text, r"const DATA = ", r";\nconst CATS")
    cm, cats_text = block(text, r"const CATS = ", r";\nconst CAT_BY_ID")
    rm, readings_text = block(text, r"const KANJI_READINGS = ", r";\n// 2026-07-20")
    data, cats, readings = json.loads(data_text), json.loads(cats_text), json.loads(readings_text)
    by_id = {c['id']: c for c in cats}
    g4, g5, g6 = by_id['g4']['chars'], by_id['g5']['chars'], by_id['g6']['chars']
    for ch in "賀群徳富城":
        for group in (g5, g6):
            if ch in group: group.remove(ch)
        if ch not in g4: g4.append(ch)
    for ch in TO5:
        g4.remove(ch); g5.append(ch)
    for ch in TO6:
        for group in (g4, g5):
            if ch in group: group.remove(ch)
        g6.append(ch)
    for ch, (on, kun, ex) in ADD.items():
        data[ch] = paths(svg_dir, ch)
        readings[ch] = {'on': on, 'kun': kun, 'ex': ex, 'grade': 4}
        if ch not in g4: g4.append(ch)
    for grade in range(1, 7):
        chars = by_id[f'g{grade}']['chars']
        by_id[f'g{grade}']['sub'] = f'{len(chars)}字'
        for ch in chars: readings[ch]['grade'] = grade
    expected = [80,160,200,202,193,191]
    assert [len(by_id[f'g{i}']['chars']) for i in range(1,7)] == expected
    assert len(set(sum((by_id[f'g{i}']['chars'] for i in range(1,7)), []))) == 1026
    assert set(data) >= set(readings) >= set(sum((by_id[f'g{i}']['chars'] for i in range(1,7)), []))
    text = text[:dm.start(1)] + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + text[dm.end(1):]
    cm, _ = block(text, r"const CATS = ", r";\nconst CAT_BY_ID")
    text = text[:cm.start(1)] + json.dumps(cats, ensure_ascii=False, separators=(',', ':')) + text[cm.end(1):]
    rm, _ = block(text, r"const KANJI_READINGS = ", r";\n// 2026-07-20")
    text = text[:rm.start(1)] + json.dumps(readings, ensure_ascii=False, separators=(',', ':')) + text[rm.end(1):]
    app.write_text(text)

if __name__ == '__main__': main()
