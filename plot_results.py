import json
from pathlib import Path

results_dir = Path("results")

json_files = list(results_dir.glob("*.json"))
if not json_files:
    raise FileNotFoundError("resultsフォルダにjsonファイルがありません")

latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

print(f"Using file: {latest_file}")

with open(latest_file, "r", encoding="utf-8") as f:
    results = json.load(f)

ms = results["ms"]
beat = results["beat"]

print()
print("===== 練習結果 =====")
print(f"平均ズレ: {ms['mean']:.1f} ms")
print(f"典型的なズレ: {ms['median']:.1f} ms")
print(f"100ms以内: {ms['100ms'] * 100:.1f}%")
print(f"300ms以内: {ms['300ms'] * 100:.1f}%")

print()
print("===== beat単位 =====")
print(f"平均ズレ: {beat['mean']:.3f} 拍")
print(f"典型的なズレ: {beat['median']:.3f} 拍")
print(f"0.3拍以内: {beat['0.3b'] * 100:.1f}%")
print(f"0.5拍以内: {beat['0.5b'] * 100:.1f}%")

print()
if ms["median"] <= 100 and ms["300ms"] >= 0.9:
    print("判定: だいたい安定して追従できています。")
elif ms["median"] <= 200:
    print("判定: 追従はできていますが、少しズレがあります。")
else:
    print("判定: ズレが大きめです。音源・楽譜・アノテーションを確認してください。")