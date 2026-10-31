# data/

- `minitab_samples/` : Minitab 지원 사이트의 샘플 데이터(.MWX). 문서 예제 출력표와 숫자를 대조하는 테스트에 쓴다.
  저작권상 저장소에 넣지 않으며 `python research/fetch_samples.py` 로 각자 내려받는다. 파일이 없으면 해당 테스트는 건너뛴다.
- .MWX 는 zip 안에 JSON(`sheet_metadata_20.json`, `sheets/0/sheet.json`)이 든 형식이다. 읽기는 `doe_core/io/mwx.py`(예정).
