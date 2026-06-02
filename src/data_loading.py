"""
data_loading.py
===============
Ham CSV veri setinin diskten okunmasindan ve ilk genel ozetinin
cikarilmasindan sorumlu modul.

Veri seti ~102.000 satir ve 28 sutundan olustugu icin WEKA/Orange gibi
masaustu araclar bellek/performans acisindan zorlanmaktadir. Bu nedenle
proje Python (pandas) ile gerceklestirilmistir.
"""

from __future__ import annotations

import io

import pandas as pd

from . import config


def load_raw_data(verbose: bool = True) -> pd.DataFrame:
    """
    Ham 'EUROPEAN_FOOTBALL_DATABASE_FULL.csv' dosyasini DataFrame olarak yukler.

    Returns
    -------
    pandas.DataFrame
        Ham veri seti (hicbir temizleme uygulanmamis hali).
    """
    if not config.DATA_FILE.exists():
        raise FileNotFoundError(
            f"Veri dosyasi bulunamadi: {config.DATA_FILE}\n"
            "EUROPEAN_FOOTBALL_DATABASE_FULL.csv dosyasi 'data/' klasorunde olmalidir."
        )

    df = pd.read_csv(config.DATA_FILE)

    if verbose:
        print("=" * 70)
        print("ADIM 1 | VERI YUKLEME")
        print("=" * 70)
        print(f"Kaynak dosya : {config.DATA_FILE.name}")
        print(f"Boyut        : {df.shape[0]:,} satir  x  {df.shape[1]} sutun")
        print(f"Bellek       : {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
        print()

    return df


def summarize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Her sutun icin tip, eksik deger sayisi/orani ve benzersiz deger sayisini
    iceren bir ozet tablosu uretir. Bu tablo "Veri Ozeti" bolumunde kullanilir.
    """
    summary = pd.DataFrame({
        "veri_tipi": df.dtypes.astype(str),
        "dolu_kayit": df.notna().sum(),
        "eksik_kayit": df.isna().sum(),
        "eksik_yuzde": (df.isna().mean() * 100).round(2),
        "benzersiz_deger": df.nunique(),
    })
    summary.index.name = "sutun"
    return summary.reset_index()


def print_info(df: pd.DataFrame) -> None:
    """pandas .info() ciktisini standart cikisa yazdirir (hizli kontrol icin)."""
    buf = io.StringIO()
    df.info(buf=buf)
    print(buf.getvalue())
