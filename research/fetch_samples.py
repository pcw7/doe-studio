"""Minitab 지원 사이트의 샘플 데이터(.MWX)를 data/minitab_samples/ 에 내려받는다.

문서 예제의 출력표(tests/fixtures/minitab_docs)와 숫자를 대조하려면 이 데이터가 필요하다.
Minitab 의 샘플 데이터는 재배포하지 않으므로 저장소에 넣지 않고 각자 내려받는다.

사용법: python research/fetch_samples.py
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

BASE = "https://support.minitab.com/en-us/datasets/media/generated-content/datasets/"
FILES = [
    "InsulationProperties.MWX",   # Analyze Factorial Design, Factorial Plots, Cube Plot, Predict, Optimizer
    "SealStrength.MWX",           # Analyze Response Surface Design, Contour/Surface, Optimizer
    "FondueRecipe.MWX",           # Analyze Mixture Design, Response Trace, Contour(mixture)
    "ultrasonic_cleaner.MWX",     # Analyze Definitive Screening Design
    "ThermalEnergyTest.MWX",      # Response Optimizer, Predict(회귀)
    "CrystalGrowth.MWX",          # Select Optimal Design
]


def main() -> int:
    out = Path(__file__).resolve().parents[1] / "data" / "minitab_samples"
    out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for name in FILES:
        dest = out / name
        if dest.exists():
            print(f"skip {name} (이미 있음)")
            continue
        try:
            with urllib.request.urlopen(BASE + name, timeout=60) as r:
                dest.write_bytes(r.read())
            print(f"ok   {name} -> {dest}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {e}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
