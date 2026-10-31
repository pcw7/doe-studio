"""요인 '단어'(ABD 같은 요인 곱) 연산. 비트마스크 int 로 표현한다.

Minitab 관례대로 요인 문자는 I 를 건너뛴다: A B C D E F G H J K L M N O P (최대 15요인).
두 단어의 곱은 XOR(같은 문자는 소거).
"""
from __future__ import annotations

LETTERS = "ABCDEFGHJKLMNOP"
ROMAN = {3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}
ROMAN_INV = {v: k for k, v in ROMAN.items()}


def word_from_str(s: str) -> int:
    mask = 0
    for ch in s.strip().upper():
        if ch not in LETTERS:
            raise ValueError(f"요인 문자가 아닙니다: {ch!r} (허용: {LETTERS})")
        mask |= 1 << LETTERS.index(ch)
    return mask


def word_to_str(mask: int) -> str:
    return "".join(LETTERS[i] for i in range(len(LETTERS)) if mask >> i & 1) or "I"


def word_len(mask: int) -> int:
    return bin(mask).count("1")


def word_key(mask: int) -> tuple[int, str]:
    """정렬 키: 차수 오름차순, 같은 차수면 알파벳순."""
    return (word_len(mask), word_to_str(mask))


def span(words: list[int]) -> list[int]:
    """단어들이 생성하는 군(항등원 I 제외), 정렬됨."""
    group = {0}
    for w in words:
        group |= {g ^ w for g in group}
    return sorted((g for g in group if g), key=word_key)


def generator_words(generators: dict[str, str]) -> list[int]:
    """{'E': 'ABC'} -> [mask('ABCE')]"""
    return [word_from_str(L + w) for L, w in generators.items()]


def resolution_of(generators: dict[str, str]) -> int | None:
    """정의관계의 최단 단어 길이. 완전 요인설계(생성자 없음)면 None."""
    return min((word_len(w) for w in span(generator_words(generators))), default=None)


def resolution_with_blocks_of(generators: dict[str, str], block_generators: list[str]) -> int:
    """블록과 교락된 가장 짧은 단어 길이 + 1."""
    dset = set(span(generator_words(generators))) | {0}
    blocks = span([word_from_str(x) for x in block_generators])
    shortest = min(word_len(b ^ w) for b in blocks for w in dset)
    return shortest + 1
