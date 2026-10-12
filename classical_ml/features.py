"""Trich dac trung cho ML co dien (Tuan 2-3).

Khung ham; dien logic khi da co dataset o data/processed/.
"""
import re

SHELL_METACHARS = set(";|&`$()<>\n")


def special_char_ratio(s: str) -> float:
    if not s:
        return 0.0
    return sum(not c.isalnum() and c != " " for c in s) / len(s)


def shell_metachar_count(s: str) -> int:
    return sum(c in SHELL_METACHARS for c in s)


def handcrafted_features(s: str) -> dict:
    """Dac trung thu cong, doc duoc, de phan tich loi False Positive."""
    return {
        "length": len(s),
        "special_char_ratio": round(special_char_ratio(s), 4),
        "shell_metachar_count": shell_metachar_count(s),
        "has_substitution": int(bool(re.search(r"\$\(|`", s))),
        "has_separator": int(bool(re.search(r"[;|]|&&", s))),
    }


# TODO (Tuan 3): dung CountVectorizer/TfidfVectorizer(analyzer="char", ngram_range=(1,3))
#               ghep voi handcrafted_features qua sklearn Pipeline/FeatureUnion.
if __name__ == "__main__":
    for demo in ["8.8.8.8", "127.0.0.1; id", "report_2024;final.pdf"]:
        print(demo, "->", handcrafted_features(demo))
