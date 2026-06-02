"""
feature_selection.py
====================
Ozellik secimi (feature selection) asamasi.

Iki tamamlayici yontemle her ozellige bir onem puani verilir ve en yuksek
puanli ilk K ozellik secilir:

  1. ANOVA F-testi (SelectKBest, f_classif):
     Her ozelligin siniflar arasinda ortalamasinin ne kadar ayristigini olcer.
     Tek degiskenli (univariate), hizli ve istatistiksel bir filtre yontemidir.

  2. Random Forest Onem Skorlari (model tabanli / embedded):
     Bir agac toplulugunun, dugum bolmelerinde her ozelligi ne siklikta ve
     ne kadar etkili kullandigini olcer. Degiskenler arasi etkilesimi de yakalar.

Secilen ozellik listesi, "tum ozellikler vs secilmis ozellikler" karsilastirmasi
icin modelleme asamasina aktarilir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import StandardScaler

from . import config
from .visualization import save_fig


def compute_importance(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """
    Her ozellik icin ANOVA F-skoru ve Random Forest onem skorunu hesaplar,
    ikisinin [0,1] araligina olceklenmis ortalamasiyla birlesik bir siralama uretir.
    """
    # 1) ANOVA F-testi
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    f_selector = SelectKBest(score_func=f_classif, k="all").fit(X_scaled, y)
    f_scores = pd.Series(f_selector.scores_, index=X.columns)

    # 2) Random Forest onem skorlari
    rf = RandomForestClassifier(
        n_estimators=200, random_state=config.RANDOM_STATE, n_jobs=-1
    ).fit(X, y)
    rf_scores = pd.Series(rf.feature_importances_, index=X.columns)

    # Iki skoru [0,1] araligina normalize edip ortalamasini al
    def norm(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else s * 0.0

    table = pd.DataFrame({
        "ozellik": X.columns,
        "anova_f": f_scores.values,
        "rf_onem": rf_scores.values,
        "anova_norm": norm(f_scores).values,
        "rf_norm": norm(rf_scores).values,
    })
    table["birlesik_skor"] = (table["anova_norm"] + table["rf_norm"]) / 2
    table = table.sort_values("birlesik_skor", ascending=False).reset_index(drop=True)
    return table


def select_features(importance: pd.DataFrame, k: int | None = None) -> list[str]:
    """Birlesik skora gore en yuksek ilk k ozelligin adlarini dondurur."""
    k = k or config.TOP_K_FEATURES
    return importance["ozellik"].head(k).tolist()


def plot_importance(importance: pd.DataFrame, selected: list[str]) -> None:
    """Ozellik onem skorlarini (birlesik) cubuk grafikle gosterir; secilenleri vurgular."""
    data = importance.iloc[::-1]  # en onemli ustte
    colors = [config.ACCENT_COLOR if f in selected else "#B0BEC5"
              for f in data["ozellik"]]
    labels_tr = [config.tr_label(f) for f in data["ozellik"]]
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.barh(labels_tr, data["birlesik_skor"], color=colors)
    ax.set_title("Özellik Önem Sıralaması (ANOVA F + Random Forest, normalize)")
    ax.set_xlabel("Birleşik Önem Skoru [0–1]")
    # Lejant
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(color=config.ACCENT_COLOR, label="Seçildi (ilk %d)" % len(selected)),
        Patch(color="#B0BEC5", label="Seçilmedi"),
    ], loc="lower right")
    save_fig(fig, "07_ozellik_onem")


def run(X: pd.DataFrame, y: pd.Series, verbose: bool = True
        ) -> tuple[list[str], pd.DataFrame]:
    """Ozellik secimi asamasini calistirir; (secilen_ozellikler, onem_tablosu) dondurur."""
    if verbose:
        print("=" * 70)
        print("ADIM 4 | OZELLIK SECIMI (FEATURE SELECTION)")
        print("=" * 70)
    importance = compute_importance(X, y)
    selected = select_features(importance)
    plot_importance(importance, selected)
    if verbose:
        print(f"Toplam ozellik       : {X.shape[1]}")
        print(f"Secilen ozellik (k={config.TOP_K_FEATURES}) : {selected}")
        print()
    return selected, importance
