"""
preprocessing.py
================
Veri hazirlama (data preparation) asamasinin tum mantigini icerir:

  1. Hedef degiskenin (mac sonucu: 1/0/2) gol sayilarindan turetilmesi
  2. Eksik veri analizi ve raporlanmasi
  3. Aykiri deger (outlier) tespiti  (IQR yontemi)
  4. Sizinti (leakage) ve gereksiz sutunlarin temizlenmesi
  5. Yeni ozelliklerin turetilmesi (feature engineering)
  6. Modelleme matrisinin (X, y) olusturulmasi (tam-kayit / complete-case)

Tasarim kararlari ilgili fonksiyonlarin docstring'lerinde gerekcelendirilmistir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


# ---------------------------------------------------------------------------
# 1) HEDEF DEGISKEN TURETME
# ---------------------------------------------------------------------------
def add_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ev sahibi ve deplasman gol sayilarini karsilastirarak mac sonucu
    (hedef sinif) sutununu ekler.

        home_goals > away_goals  ->  1  (Ev Sahibi Galibiyeti)
        home_goals == away_goals ->  0  (Beraberlik)
        home_goals < away_goals  ->  2  (Deplasman Galibiyeti)

    Not: home_goals ve away_goals sutunlari hedefi DOGRUDAN belirledigi icin
    daha sonra ozellik kumesinden cikarilir (bkz. config.LEAKAGE_COLS).
    """
    df = df.copy()
    conditions = [
        df["home_goals"] > df["away_goals"],
        df["home_goals"] == df["away_goals"],
    ]
    df[config.TARGET_COL] = np.select(conditions, [1, 0], default=2).astype(int)
    return df


# ---------------------------------------------------------------------------
# 2) EKSIK VERI ANALIZI
# ---------------------------------------------------------------------------
def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sutun bazinda eksik deger sayisi ve oranini iceren, orana gore azalan
    sirali bir rapor dondurur.
    """
    report = pd.DataFrame({
        "eksik_sayi": df.isna().sum(),
        "eksik_yuzde": (df.isna().mean() * 100).round(2),
    })
    report.index.name = "sutun"
    return report.sort_values("eksik_yuzde", ascending=False).reset_index()


# ---------------------------------------------------------------------------
# 3) AYKIRI DEGER (OUTLIER) TESPITI
# ---------------------------------------------------------------------------
def detect_outliers_iqr(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    IQR (Interquartile Range / Ceyrekler Acikligi) yontemiyle her sayisal
    sutundaki aykiri deger sayisini hesaplar.

    Bir x degeri su araligin disinda ise aykiri kabul edilir:
        [Q1 - 1.5*IQR , Q3 + 1.5*IQR]      IQR = Q3 - Q1

    Returns
    -------
    Her sutun icin alt/ust sinir ve aykiri deger sayisi/orani tablosu.
    """
    rows = []
    for col in columns:
        if col not in df.columns:
            continue
        s = df[col].dropna()
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (s < low) | (s > high)
        rows.append({
            "sutun": col,
            "alt_sinir": round(low, 2),
            "ust_sinir": round(high, 2),
            "aykiri_sayi": int(mask.sum()),
            "aykiri_yuzde": round(mask.mean() * 100, 2),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4) OZELLIK TURETME (FEATURE ENGINEERING)
# ---------------------------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ham degiskenlerden, mac sonucunu daha iyi aciklayan yeni ozellikler turetir:

    * Ima edilen olasiliklar (implied probabilities):
        Bahis orani 'odds' -> olasilik '1/odds'. Uc sonucun ham olasiliklari
        toplami 1'den buyuktur (bahis ofisi kar marji - "overround"). Bu yuzden
        normalize edilir. Bu deger, piyasanin maca dair beklentisini ozetler.

    * Fark (difference) ozellikleri:
        Ev ve deplasman istatistiklerinin farki, sahadaki goreli ustunlugu
        tek bir sayida ozetler (orn. sut farki, isabetli sut farki, korner farki).
    """
    df = df.copy()

    # Ima edilen (normalize) olasiliklar
    inv_h = 1.0 / df["odds_home"]
    inv_d = 1.0 / df["odds_draw"]
    inv_a = 1.0 / df["odds_away"]
    overround = inv_h + inv_d + inv_a
    df["implied_prob_home"] = inv_h / overround
    df["implied_prob_draw"] = inv_d / overround
    df["implied_prob_away"] = inv_a / overround

    # Goreli ustunluk (fark) ozellikleri
    df["shots_diff"] = df["home_shots"] - df["away_shots"]
    df["shots_target_diff"] = df["home_shots_target"] - df["away_shots_target"]
    df["corners_diff"] = df["home_corners"] - df["away_corners"]

    return df


# ---------------------------------------------------------------------------
# 5) ANA TEMIZLEME / HAZIRLAMA HATTI
# ---------------------------------------------------------------------------
def build_modeling_frame(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Ham veriden modellemeye hazir, tam-kayit (complete-case) bir cerceve uretir.

    Adimlar
    -------
    1. Hedef degisken eklenir (add_target).
    2. Modelleme icin gerekli ham sayisal ozellikler (oranlar + mac
       istatistikleri) belirlenir.
    3. Bu ozelliklerde eksik degeri olan satirlar cikarilir (complete-case).
       Gerekce: mac istatistiklerinde eksiklik ~%42 oldugundan, bu kadar
       buyuk oranli atama (imputation) yapilan ham sinyali bozar. ~55.000
       kayitlik tam alt kume hem yeterince buyuk hem de daha guvenilirdir.
       (Medyan ile atama alternatifi raporda tartisilmaktadir.)
    4. Turetilmis ozellikler eklenir (engineer_features).
    5. Yalnizca model girdileri (ozellikler + hedef) tutulur.
    """
    if verbose:
        print("=" * 70)
        print("ADIM 3 | VERI HAZIRLAMA (TEMIZLEME + OZELLIK TURETME)")
        print("=" * 70)

    n_start = len(df)
    df = add_target(df)

    # Modelleme icin gerekli ham ozellikler eksiksiz olmali
    needed = config.REQUIRED_FEATURE_COLS
    complete = df.dropna(subset=needed).copy()

    if verbose:
        print(f"Baslangic satir sayisi          : {n_start:,}")
        print(f"Oran + mac ist. eksiksiz satir  : {len(complete):,} "
              f"(%{len(complete)/n_start*100:.1f})")
        print(f"Cikarilan (eksik) satir sayisi  : {n_start - len(complete):,}")

    # Turetilmis ozellikler
    complete = engineer_features(complete)

    # Nihai ozellik listesi: ham (oran + mac ist.) + turetilmis
    feature_cols = config.REQUIRED_FEATURE_COLS + config.ENGINEERED_COLS
    keep_cols = feature_cols + [config.TARGET_COL]
    modeling = complete[keep_cols].reset_index(drop=True)

    # Sonsuz/NaN guvenlik kontrolu (turetmeden kaynakli)
    modeling = modeling.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)

    if verbose:
        print(f"Nihai ozellik sayisi            : {len(feature_cols)} "
              f"({len(config.REQUIRED_FEATURE_COLS)} ham + "
              f"{len(config.ENGINEERED_COLS)} turetilmis)")
        print(f"Nihai modelleme matrisi         : {modeling.shape[0]:,} x "
              f"{modeling.shape[1]}")
        print()

    return modeling


def split_X_y(modeling: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Modelleme cercevesini ozellik matrisi (X) ve hedef vektore (y) ayirir."""
    X = modeling.drop(columns=[config.TARGET_COL])
    y = modeling[config.TARGET_COL]
    return X, y
