"""Tokenize payload o MUC KY TU cho CNN-1D (Tuan 2-3)."""
MAX_LEN = 200  # cat/pad ve do dai co dinh


def build_vocab(texts):
    chars = sorted({c for t in texts for c in t})
    # 0 = padding, 1 = ky tu la (unknown)
    return {c: i + 2 for i, c in enumerate(chars)}


def encode(text, vocab, max_len=MAX_LEN):
    ids = [vocab.get(c, 1) for c in text[:max_len]]
    return ids + [0] * (max_len - len(ids))


if __name__ == "__main__":
    v = build_vocab(["127.0.0.1; id", "8.8.8.8"])
    print("vocab size:", len(v))
    print(encode("127.0.0.1; id", v)[:16], "...")
