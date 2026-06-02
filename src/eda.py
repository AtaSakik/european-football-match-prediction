"""
eda.py
======
Kesifsel Veri Analizi (Exploratory Data Analysis).

Bu modul ham/temizlenmis veri uzerinden raporda kullanilacak acIklayici
gorselleri uretir ve outputs/figures altina kaydeder:

  01  Sinif (hedef) dagilimi
  02  Liglere gore mac sayisi
  03  Sutun bazli eksik veri orani
  04  Mac istatistikleri icin aykiri deger kutu grafikleri (boxplot)
  05  Ozellikler arasi korelasyon isi haritasi (heatmap)
  06  Ima edilen ev sahibi galibiyet olasiligi - gercek sonuca gore dagilim
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from . import config
from .visualization import save_fig


def plot_class_distribution(df: pd.DataFrame) -> None:
    """Hedef sinifin (mac sonucu) dagilimini cubuk grafikle gosterir."""
    counts = df[config.TARGET_COL].value_counts().reindex(config.CLASS_ORDER)
    labels = [config.CLASS_LABELS[c] for c in config.CLASS_ORDER]
    colors = [config.CLASS_COLORS[c] for c in config.CLASS_ORDER]
    pct = counts / counts.sum() * 100

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, counts.values, color=colors, edgecolor="white")
    for bar, c, p in zip(bars, counts.values, pct.values):
        ax.text(bar.get_x() + bar.get_width() / 2, c + counts.max() * 0.01,
                f"{c:,}\n(%{p:.1f})", ha="center", va="bottom", fontweight="bold")
    ax.set_title("Hedef Değişken Dağılımı: Maç Sonucu")
    ax.set_ylabel("Maç Sayısı")
    ax.set_ylim(0, counts.max() * 1.15)
    ax.margins(y=0.1)
    # Cogunluk-sinif taban dogrulugunu not olarak ekle
    base = pct.max()
    ax.text(0.99, 0.95, f"Çoğunluk-sınıf taban doğruluğu: %{base:.1f}",
            transform=ax.transAxes, ha="right", va="top",
            bbox=dict(boxstyle="round", fc="#FFF3CD", ec="#E0A800"))
    save_fig(fig, "01_sinif_dagilimi")


def plot_league_distribution(df: pd.DataFrame, top: int = 15) -> None:
    """En cok maca sahip liglerin yatay cubuk grafigi."""
    counts = df["league"].value_counts().head(top)[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(counts.index, counts.values, color=config.PRIMARY_COLOR)
    for i, v in enumerate(counts.values):
        ax.text(v + counts.max() * 0.01, i, f"{v:,}", va="center", fontsize=9)
    ax.set_title(f"En Çok Maça Sahip {top} Lig")
    ax.set_xlabel("Maç Sayısı")
    ax.set_xlim(0, counts.max() * 1.1)
    save_fig(fig, "02_lig_dagilimi")


def plot_missing_values(missing_df: pd.DataFrame) -> None:
    """Sutun bazli eksik veri oranini gosterir (yalnizca eksigi olanlar)."""
    data = missing_df[missing_df["eksik_yuzde"] > 0].sort_values("eksik_yuzde")
    if data.empty:
        return
    colors = ["#E63946" if v > 50 else "#F4A261" if v > 20 else "#2A9D8F"
              for v in data["eksik_yuzde"]]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(data["sutun"], data["eksik_yuzde"], color=colors)
    for i, v in enumerate(data["eksik_yuzde"]):
        ax.text(v + 0.5, i, f"%{v:.1f}", va="center", fontsize=9)
    ax.axvline(50, color="#E63946", ls="--", lw=1, alpha=0.7)
    ax.set_title("Sütun Bazlı Eksik Veri Oranı")
    ax.set_xlabel("Eksik Veri Yüzdesi (%)")
    ax.set_xlim(0, max(data["eksik_yuzde"].max() * 1.15, 10))
    save_fig(fig, "03_eksik_veri")


def plot_outlier_boxplots(df: pd.DataFrame) -> None:
    """Secili mac istatistikleri icin aykiri deger kutu grafikleri."""
    cols = ["home_shots", "away_shots", "home_shots_target", "away_shots_target",
            "home_corners", "away_corners", "home_fouls", "away_fouls"]
    cols = [c for c in cols if c in df.columns]
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    for ax, col in zip(axes.ravel(), cols):
        sns.boxplot(y=df[col], ax=ax, color=config.PRIMARY_COLOR, width=0.5,
                    flierprops=dict(marker="o", markersize=3, alpha=0.3))
        ax.set_title(col, fontsize=10)
        ax.set_ylabel("")
    fig.suptitle("Maç İstatistiklerinde Aykırı Değer Analizi (Kutu Grafikleri)")
    save_fig(fig, "04_aykiri_deger_boxplot")


def plot_correlation_heatmap(modeling: pd.DataFrame) -> None:
    """Modelleme ozellikleri + hedef arasi Pearson korelasyon isi haritasi."""
    corr = modeling.corr(numeric_only=True)
    tr_names = [config.tr_label(c) for c in corr.columns]
    corr.index = tr_names
    corr.columns = tr_names
    fig, ax = plt.subplots(figsize=(14, 12))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, cmap="RdBu_r", center=0, vmin=-1, vmax=1,
                annot=True, fmt=".2f", annot_kws={"size": 6.5}, square=True,
                linewidths=0.5, cbar_kws={"shrink": 0.7, "label": "Pearson r"}, ax=ax)
    ax.set_title("Özellikler Arası Korelasyon Isı Haritası")
    save_fig(fig, "05_korelasyon_haritasi")


def plot_implied_prob_vs_result(modeling: pd.DataFrame) -> None:
    """
    Bahis piyasasinin ev sahibine bicttigi olasiligin, gercek sonuca gore
    dagilimi. Piyasa sinyalinin ayirt edici gucunu gorsellestirir.
    """
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for c in config.CLASS_ORDER:
        sub = modeling[modeling[config.TARGET_COL] == c]["implied_prob_home"]
        sns.kdeplot(sub, ax=ax, fill=True, alpha=0.35,
                    color=config.CLASS_COLORS[c], label=config.CLASS_LABELS[c],
                    linewidth=1.8)
    ax.set_title("İma Edilen Ev Sahibi Galibiyet Olasılığı — Gerçek Sonuca Göre")
    ax.set_xlabel("İma Edilen Ev Sahibi Galibiyet Olasılığı (1/oran, normalize)")
    ax.set_ylabel("Yoğunluk")
    ax.legend(title="Gerçek Maç Sonucu")
    save_fig(fig, "06_oran_olasilik_dagilimi")


def run_all(raw_df: pd.DataFrame, modeling: pd.DataFrame,
            missing_df: pd.DataFrame, verbose: bool = True) -> None:
    """Tum EDA gorsellerini sirayla uretir."""
    if verbose:
        print("=" * 70)
        print("ADIM 2 | KESIFSEL VERI ANALIZI (GORSELLER)")
        print("=" * 70)
    plot_class_distribution(raw_df)
    plot_league_distribution(raw_df)
    plot_missing_values(missing_df)
    plot_outlier_boxplots(raw_df)
    plot_correlation_heatmap(modeling)
    plot_implied_prob_vs_result(modeling)
    if verbose:
        print()
