"""
modeling.py
===========
Model kurulumu, egitimi ve degerlendirmesi.

Karsilastirma icin 6 farkli sinif siniflandirma algoritmasi kullanilir
(proje onerisinde belirtilen Karar Agaci, Random Forest ve Naive Bayes
zorunlu olarak dahildir):

    1. Decision Tree        (Karar Agaci)
    2. Random Forest        (Rastgele Orman)
    3. Naive Bayes          (Gaussian)
    4. Logistic Regression  (Lojistik Regresyon)
    5. K-Nearest Neighbors  (K-En Yakin Komsu)
    6. Gradient Boosting    (HistGradientBoosting)

Her algoritma iki ozellik kumesiyle egitilir:
    (a) TUM ozellikler
    (b) SECILMIS ozellikler (feature_selection modulunden)

Boylece ozellik seciminin dogruluga etkisi tablo halinde karsilastirilir.
Olceklemeye duyarli modeller (LogReg, KNN) icin StandardScaler bir Pipeline
icinde kullanilir; agac tabanli modeller olcekleme gerektirmez.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from . import config
from .visualization import save_fig


# ---------------------------------------------------------------------------
# MODEL TANIMLARI
# ---------------------------------------------------------------------------
def build_models() -> dict[str, Pipeline]:
    """
    Algoritma adi -> sklearn Pipeline esleyen sozluk uretir.
    Olceklemeye duyarli modeller StandardScaler ile sarmalanir.
    """
    rs = config.RANDOM_STATE
    return {
        "Karar Ağacı": Pipeline([
            ("clf", DecisionTreeClassifier(max_depth=12, random_state=rs)),
        ]),
        "Random Forest": Pipeline([
            ("clf", RandomForestClassifier(n_estimators=300, random_state=rs, n_jobs=-1)),
        ]),
        "Naive Bayes": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GaussianNB()),
        ]),
        "Lojistik Regresyon": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=rs)),
        ]),
        "K-En Yakın Komşu": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", KNeighborsClassifier(n_neighbors=25)),
        ]),
        "Gradient Boosting": Pipeline([
            ("clf", HistGradientBoostingClassifier(random_state=rs)),
        ]),
    }


# ---------------------------------------------------------------------------
# TEK BIR OZELLIK KUMESI ICIN TUM MODELLERI DEGERLENDIR
# ---------------------------------------------------------------------------
def evaluate_models(X_train, X_test, y_train, y_test, feature_set_name: str,
                    cv: bool = True, verbose: bool = True) -> pd.DataFrame:
    """
    Tum modelleri verilen egitim/test bolmesi uzerinde egitir ve degerlendirir.

    Returns
    -------
    Her model icin dogruluk (accuracy), makro-F1, 5-katli CV ortalamasi ve
    egitim suresini iceren bir sonuc tablosu.
    """
    rows = []
    for name, model in build_models().items():
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        fit_time = time.perf_counter() - t0

        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")

        cv_mean = cv_std = np.nan
        if cv:
            cv_scores = cross_val_score(model, X_train, y_train,
                                        cv=config.CV_FOLDS, scoring="accuracy",
                                        n_jobs=-1)
            cv_mean, cv_std = cv_scores.mean(), cv_scores.std()

        rows.append({
            "Özellik Kümesi": feature_set_name,
            "Algoritma": name,
            "Doğruluk (Accuracy)": round(acc, 4),
            "Makro F1": round(f1, 4),
            "CV Ort. Doğruluk": round(cv_mean, 4),
            "CV Std": round(cv_std, 4),
            "Eğitim Süresi (sn)": round(fit_time, 3),
        })
        if verbose:
            print(f"   [{feature_set_name:18s}] {name:20s} "
                  f"acc={acc:.4f}  F1={f1:.4f}  CV={cv_mean:.4f}")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ANA DEGERLENDIRME: TUM vs SECILMIS OZELLIKLER
# ---------------------------------------------------------------------------
def run(X: pd.DataFrame, y: pd.Series, selected_features: list[str],
        verbose: bool = True) -> dict:
    """
    'Tum ozellikler' ve 'secilmis ozellikler' kumeleri icin tum modelleri
    egitir, sonuc tablosunu ve en iyi model bilgisini dondurur.
    """
    if verbose:
        print("=" * 70)
        print("ADIM 5 | MODEL EGITIMI VE DEGERLENDIRME")
        print("=" * 70)

    # Egitim/test bolmesi (stratified -> sinif oranlari korunur)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE,
        stratify=y,
    )
    if verbose:
        print(f"Egitim seti: {X_train.shape[0]:,} | Test seti: {X_test.shape[0]:,}")
        print(f"Cogunluk-sinif taban dogrulugu (test): "
              f"%{y_test.value_counts(normalize=True).max()*100:.2f}\n")

    # (a) Tum ozellikler
    res_all = evaluate_models(X_train, X_test, y_train, y_test,
                              "Tüm Özellikler", verbose=verbose)
    if verbose:
        print()
    # (b) Secilmis ozellikler
    res_sel = evaluate_models(X_train[selected_features], X_test[selected_features],
                              y_train, y_test, "Seçilmiş Özellikler", verbose=verbose)

    results = pd.concat([res_all, res_sel], ignore_index=True)

    # En iyi modeli (tum ozellikler kumesinde, dogruluga gore) belirle
    best_row = res_all.loc[res_all["Doğruluk (Accuracy)"].idxmax()]
    best_name = best_row["Algoritma"]
    best_model = build_models()[best_name].fit(X_train, y_train)
    best_pred = best_model.predict(X_test)

    if verbose:
        print(f"\nEn iyi model: {best_name} "
              f"(dogruluk %{best_row['Doğruluk (Accuracy)']*100:.2f})\n")

    return {
        "results": results,
        "res_all": res_all,
        "res_sel": res_sel,
        "best_name": best_name,
        "best_model": best_model,
        "y_test": y_test,
        "best_pred": best_pred,
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train,
        "baseline": y_test.value_counts(normalize=True).max(),
    }


# ---------------------------------------------------------------------------
# SONUC GORSELLERI
# ---------------------------------------------------------------------------
def plot_accuracy_comparison(results: pd.DataFrame) -> None:
    """Algoritma x ozellik-kumesi dogruluk karsilastirma cubuk grafigi."""
    pivot = results.pivot(index="Algoritma", columns="Özellik Kümesi",
                          values="Doğruluk (Accuracy)")
    pivot = pivot.sort_values("Tüm Özellikler", ascending=False)
    pivot = pivot[["Tüm Özellikler", "Seçilmiş Özellikler"]]  # sutun sirasi
    fig, ax = plt.subplots(figsize=(11, 6))
    pivot.plot(kind="bar", ax=ax, color=[config.PRIMARY_COLOR, config.ACCENT_COLOR],
               edgecolor="white", width=0.78)
    ax.set_title("Algoritmaların Doğruluk Karşılaştırması: Tüm vs Seçilmiş Özellikler")
    ax.set_ylabel("Test Doğruluğu (Accuracy)")
    ax.set_xlabel("")
    ax.set_ylim(0, max(pivot.max()) * 1.18)
    ax.legend(title="Özellik Kümesi")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", fontsize=8, padding=2)
    save_fig(fig, "08_dogruluk_karsilastirma")


def plot_confusion_matrix(y_test, y_pred, model_name: str) -> None:
    """En iyi model icin karmasiklik matrisini (normalize) cizer."""
    cm = confusion_matrix(y_test, y_pred, labels=config.CLASS_ORDER)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
    labels = [config.CLASS_SHORT[c] for c in config.CLASS_ORDER]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    sns.heatmap(cm, annot=True, fmt=",d", cmap="Blues", cbar=False,
                xticklabels=labels, yticklabels=labels, ax=axes[0],
                annot_kws={"size": 11})
    axes[0].set_title(f"Karmaşıklık Matrisi (Sayılar) — {model_name}")
    axes[0].set_xlabel("Tahmin Edilen"); axes[0].set_ylabel("Gerçek")

    sns.heatmap(cm_norm, annot=True, fmt=".2%", cmap="Blues", cbar=False,
                xticklabels=labels, yticklabels=labels, ax=axes[1],
                vmin=0, vmax=1, annot_kws={"size": 11})
    axes[1].set_title("Karmaşıklık Matrisi (Satıra Göre Normalize)")
    axes[1].set_xlabel("Tahmin Edilen"); axes[1].set_ylabel("Gerçek")
    save_fig(fig, "09_karmasiklik_matrisi")


def classification_report_df(y_test, y_pred) -> pd.DataFrame:
    """Sinif bazli precision/recall/F1 raporunu DataFrame olarak dondurur."""
    rep = classification_report(
        y_test, y_pred, labels=config.CLASS_ORDER,
        target_names=[config.CLASS_LABELS[c] for c in config.CLASS_ORDER],
        output_dict=True, zero_division=0,
    )
    return pd.DataFrame(rep).transpose().round(4)
