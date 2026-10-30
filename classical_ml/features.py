"""
Hai nhom dac trung, ghep lai bang FeatureUnion (build_features):
  1. Char n-gram TF-IDF  : bat chuoi ky tu dac trung cua payload
  2. Dac trung thu cong  : doc duoc, de phan tich loi False Positive
     (do dai, ty le ky tu dac biet, so metachar shell, co thay the lenh, co dau noi)

Moi phep fit (TF-IDF vocab/IDF, StandardScaler) nam TRONG Pipeline, nen khi goi
pipeline.fit(X_train) thi chi hoc tu tap train — khong ro ri sang val/test.
"""
import re

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler

SHELL_METACHARS = set(";|&`$()<>\n")
# Dau noi lenh theo dung quy tac nhan cua dataset: ; | & xuong dong (that hoac '\n' dang chu)
SEPARATOR_RE = re.compile(r"[;|&\n]|\\n")
SUBSTITUTION_RE = re.compile(r"\$\(|`")

HANDCRAFTED_NAMES = ["length", "special_char_ratio", "shell_metachar_count",
                     "has_substitution", "has_separator"]


def special_char_ratio(s: str) -> float:
    """Ty le ky tu KHONG phai chu/so/khoang trang (tinh ca . / - :) tren do dai chuoi."""
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
        "has_substitution": int(bool(SUBSTITUTION_RE.search(s))),
        "has_separator": int(bool(SEPARATOR_RE.search(s))),
    }


class Handcrafted(BaseEstimator, TransformerMixin):
    """Bien danh sach chuoi thanh ma tran 5 dac trung thu cong (dung trong Pipeline)."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array([[handcrafted_features(s)[k] for k in HANDCRAFTED_NAMES] for s in X], dtype=float)

    def get_feature_names_out(self, input_features=None):
        return np.array(HANDCRAFTED_NAMES)


def build_features(ngram_range=(1, 3), max_features=50000, use_handcrafted=True):
    """TF-IDF char n-gram + 5 dac trung thu cong (da chuan hoa).
    use_handcrafted=False -> chi TF-IDF (thi nghiem bo dac trung thu cong, vi has_separator /
    has_substitution gan nhu trung voi quy tac gan nhan cua dataset)."""
    tfidf = TfidfVectorizer(analyzer="char", ngram_range=ngram_range, lowercase=False,
                            min_df=2, sublinear_tf=True, max_features=max_features)
    if not use_handcrafted:
        return FeatureUnion([("tfidf", tfidf)])
    hand = Pipeline([("hand", Handcrafted()), ("scale", StandardScaler())])
    return FeatureUnion([("tfidf", tfidf), ("handcrafted", hand)])


if __name__ == "__main__":
    for demo in ["8.8.8.8", "127.0.0.1; id", "report_2024;final.pdf", "a & b", "x\nid"]:
        print(repr(demo), "->", handcrafted_features(demo))
    f = build_features().fit(["8.8.8.8", "127.0.0.1; id", "report;final.pdf", "8.8.4.4"])
    print("So chieu dac trung (vi du nho):", f.transform(["127.0.0.1; id"]).shape)