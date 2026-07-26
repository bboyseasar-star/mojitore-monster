#!/usr/bin/env python3
"""Verify the embedded KanjiVG and EDRDG-derived display data.

This program deliberately validates the child-facing, curated subset rather
than replacing it with every reading or every word in the source dictionaries.
It is run after each official-source acquisition; a failure means the app data
must be reviewed before release.
"""
import argparse
import gzip
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


REPAIRS = {
    "刀": {"ex": "刀剣（とうけん）"},
    "里": {"ex": "里山（さとやま）"},
    "旧": {"ex": "旧友（きゅうゆう）"},
    "統": {"kun": "すべる"},
}
EXPECTED_KANJIVG_REVISION = "d95a97627fd9fe5b2c8d06ca81e38149609c0c1e"
EXPECTED_KANJIDIC2_SHA256 = "12cbd54ca51967cf2ead06b97e816a2d6e0a25757c4eb0a07df4272d2f2e1428"
EXPECTED_JMDICT_SHA256 = "b835226b13a6c661001df83dddee281198b2a2871e44fdc2200dd547d7dccdb9"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def embedded_readings(app_path):
    text = Path(app_path).read_text(encoding="utf-8")
    match = re.search(r"const KANJI_READINGS = (\{.*\});\n// 2026-07-20", text)
    if not match:
        raise ValueError("KANJI_READINGS block was not found")
    readings = json.loads(match.group(1))
    for char, repair in REPAIRS.items():
        readings[char].update(repair)
    data_match = re.search(r"const DATA = (\{[\s\S]*?\});\nconst CATS", text)
    if not data_match:
        raise ValueError("DATA block was not found")
    return json.loads(data_match.group(1)), readings


def source_readings(kanjidic_path):
    result = {}
    with gzip.open(kanjidic_path, "rb") as source:
        root = ET.parse(source).getroot()
    for character in root.findall("character"):
        literal = character.findtext("literal")
        result[literal] = {"on": set(), "kun": set()}
        for reading in character.findall("reading_meaning/rmgroup/reading"):
            kind = reading.attrib.get("r_type")
            if kind == "ja_on":
                result[literal]["on"].add(reading.text.replace(".", "-"))
            elif kind == "ja_kun":
                result[literal]["kun"].add(reading.text.replace(".", "-"))
    return result


def normalized(values):
    if values == "なし":
        return set()
    return {value.replace("-", "") for value in values.split("・")}


def verify_kanjivg(data, readings, directory):
    failures = []
    try:
        revision = subprocess.run(
            ["git", "-C", str(Path(directory).parent), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True
        ).stdout.strip()
        if revision != EXPECTED_KANJIVG_REVISION:
            failures.append(f"KanjiVG revision mismatch: {revision}")
    except (OSError, subprocess.CalledProcessError):
        failures.append("KanjiVG revision could not be verified")
    for char in readings:
        svg_path = Path(directory) / f"{ord(char):05x}.svg"
        if not svg_path.exists():
            failures.append(f"KanjiVG SVG missing: {char}")
            continue
        paths = [element.attrib["d"] for element in ET.parse(svg_path).getroot().iter()
                 if element.tag.endswith("path") and "d" in element.attrib]
        if data.get(char) != paths:
            failures.append(f"KanjiVG path mismatch: {char}")
    return failures


def verify_jmdict(readings, jmdict_path):
    wanted_by_word = {}
    for value in readings.values():
        match = re.fullmatch(r"(.+)（(.+)）", value["ex"])
        if not match:
            raise ValueError(f"Example format is invalid: {value['ex']}")
        word, reading = match.groups()
        wanted_by_word.setdefault(word, set()).add(reading)
    found = set()
    with gzip.open(jmdict_path, "rb") as source:
        for _, entry in ET.iterparse(source, events=("end",)):
            if entry.tag != "entry":
                continue
            spellings = {node.text for node in entry.findall("k_ele/keb") if node.text}
            for word in spellings & wanted_by_word.keys():
                for reading_element in entry.findall("r_ele"):
                    reading = reading_element.findtext("reb")
                    restrictions = {node.text for node in reading_element.findall("re_restr") if node.text}
                    if reading in wanted_by_word[word] and (not restrictions or word in restrictions):
                        found.add((word, reading))
            entry.clear()
    wanted = {(word, reading) for word, readings_for_word in wanted_by_word.items()
              for reading in readings_for_word}
    return [f"JMdict example missing: {word}（{reading}）" for word, reading in sorted(wanted - found)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default="index.html")
    parser.add_argument("--kanjivg-dir", required=True)
    parser.add_argument("--kanjidic2", required=True)
    parser.add_argument("--jmdict", required=True)
    args = parser.parse_args()
    data, readings = embedded_readings(args.app)
    source = source_readings(args.kanjidic2)
    failures = verify_kanjivg(data, readings, args.kanjivg_dir)
    kanjidic_hash = sha256(args.kanjidic2)
    jmdict_hash = sha256(args.jmdict)
    if kanjidic_hash != EXPECTED_KANJIDIC2_SHA256:
        failures.append("KANJIDIC2 SHA-256 mismatch")
    if jmdict_hash != EXPECTED_JMDICT_SHA256:
        failures.append("JMdict SHA-256 mismatch")
    for char, value in readings.items():
        for kind in ("on", "kun"):
            supplied = normalized(value[kind])
            available = {item.replace("-", "") for item in source.get(char, {}).get(kind, set())}
            if not supplied.issubset(available):
                failures.append(f"KANJIDIC2 {kind} mismatch: {char}")
    failures.extend(verify_jmdict(readings, args.jmdict))
    print(f"KANJIDIC2 SHA-256: {kanjidic_hash}")
    print(f"JMdict SHA-256: {jmdict_hash}")
    print(f"Verified KanjiVG paths: {len(readings)} characters")
    print(f"Verified curated readings: {len(readings)} characters")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("Verification passed.")


if __name__ == "__main__":
    main()
