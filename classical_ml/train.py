"""Train ML co dien (SVM, RandomForest) - KHUNG, dien o Tuan 3.

Luong: doc data/processed/*.csv + train_test_split -> vectorize (features.py)
       -> fit -> luu .pkl vao models/ -> ghi du doan theo schema chung vao results/.
Co dinh random_state de tai lap.
"""
SEED = 42
# TODO: doc split, build pipeline (char n-gram TF-IDF + handcrafted), fit SVM/RF,
#       luu model, ghi results/*.csv theo schema: payload_id,model,prediction,confidence,true_label,exp
if __name__ == "__main__":
    print("Skeleton - dien o Tuan 3. Xem features.py cho dac trung.")
