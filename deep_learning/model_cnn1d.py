"""CNN-1D muc ky tu - KHUNG (Tuan 3). Can PyTorch (cai rieng, xem README).

Kien truc tham khao: Kim (2014) + eXpose (Saxe & Berlin 2017):
  Embedding -> nhieu Conv1d (kernel 3/4/5) -> max-pool -> concat -> dense -> sigmoid.
"""
try:
    import torch
    import torch.nn as nn

    class CharCNN1D(nn.Module):
        def __init__(self, vocab_size, emb_dim=32, n_filters=64,
                     kernels=(3, 4, 5), n_class=2):
            super().__init__()
            self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
            self.convs = nn.ModuleList(
                [nn.Conv1d(emb_dim, n_filters, k) for k in kernels])
            self.drop = nn.Dropout(0.5)
            self.fc = nn.Linear(n_filters * len(kernels), n_class)

        def forward(self, x):
            e = self.emb(x).transpose(1, 2)              # (B, emb, L)
            feats = [c(e).relu().max(dim=2).values for c in self.convs]
            return self.fc(self.drop(torch.cat(feats, dim=1)))

    if __name__ == "__main__":
        m = CharCNN1D(vocab_size=128)
        print(m(torch.randint(0, 128, (4, 200))).shape)  # -> (4, 2)
except ImportError:
    if __name__ == "__main__":
        print("Chua cai torch. Xem README muc Cai dat.")
