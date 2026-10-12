# Đề cương thực nghiệm T05 (2–3 trang)

## 1. Bài toán & phạm vi
Phát hiện OS Command Injection ở **mức payload** (phân loại chuỗi), so sánh 3 hướng:
Semgrep (rule-based, đầu vào mã nguồn), ML cổ điển và CNN-1D (đầu vào chuỗi payload).
Ngoài phạm vi: context-aware analysis, Windows cmd/PowerShell, firmware, Transformer/LLM.

## 2. Câu hỏi nghiên cứu
- RQ0: benchmark tĩnh có giữ được trên traffic thật từ lab không? (Exp.6)
- RQ1: model phân biệt ngữ pháp CI với SQLi/XSS không? (Exp.5)
- RQ2: FPR trên benign "khó" là bao nhiêu? (Exp.3)
- RQ3: bypass rate theo từng nhóm né tránh? (Exp.4)
- RQ4: DL học ký tự hay chuỗi có nghĩa? (SHAP/LIME, Tuần 5)

## 3. Dữ liệu
Nguồn: PayloadsAllTheThings, Commix (dương); CSIC 2010 (benign, chỉ request normal);
ECML/PKDD 2007 (CI + SQLi/XSS có nhãn); benign "khó" viết tay độc lập.
Chia 70/15/15 theo `group_id`, kiểm tra rò rỉ (split_and_check.py).

## 4. Sáu thực nghiệm
Exp.1 Semgrep trên testcase mã nguồn · Exp.2 train/eval ML+DL trên test set chuẩn ·
Exp.3 FPR trên benign khó · Exp.4 bypass rate · Exp.5 SQLi/XSS · Exp.6 traffic thật.

## 5. Chỉ số
Accuracy/Precision/Recall/F1 + FPR (trên benign khó) + bypass rate (mẫu số = payload
né tránh đã chạy được lệnh). Cố định seed, báo cáo trung bình ± độ lệch.

## 6. Schema kết quả
- ML + DL (chung): `payload_id, model, prediction, confidence, true_label, exp`
- Semgrep (riêng): `file, line, rule_id, matched, true_label, outcome` — không confidence.

## 7. Kế hoạch tái lập
README đầy đủ, requirements.lock, docker-compose một lệnh, lab mạng cách ly.
