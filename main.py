"""
main.py
=======
YMH340 Veri Madenciligi Donem Projesi - ANA CALISTIRMA DOSYASI

Avrupa Futbol Liglerinde Mac Sonucunun (Ev Sahibi Galibiyeti / Beraberlik /
Deplasman Galibiyeti) makine ogrenmesi algoritmalari ve bahis oranlari ile
tahmin edilmesi.

Bu dosya tum veri madenciligi hattini bastan sona, sirayla calistirir:

    1) Veri yukleme           (data_loading)
    2) Kesifsel veri analizi  (eda)
    3) Veri hazirlama         (preprocessing)
    4) Ozellik secimi         (feature_selection)
    5) Model egitimi/degerl.  (modeling)
    6) Sonuclarin tablolanmasi ve kaydedilmesi

Uretilen tum gorseller  -> outputs/figures/
Uretilen tum tablolar   -> outputs/tables/
Kaydedilen en iyi model -> outputs/models/

Kullanim:
    python main.py
"""

from __future__ import annotations

import sys
import warnings

import joblib
import pandas as pd

from src import config, data_loading, eda, feature_selection, modeling, preprocessing
from src.visualization import setup_style

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> None:
    """Bir tabloyu hem CSV hem de okunabilir Markdown olarak kaydeder."""
    config.ensure_directories()
    csv_path = config.TABLES_DIR / f"{name}.csv"
    md_path = config.TABLES_DIR / f"{name}.md"
    df.to_csv(csv_path, index=index, encoding="utf-8-sig")
    try:
        md_path.write_text(df.to_markdown(index=index), encoding="utf-8")
    except Exception:
        pass
    print(f"   [tablo] kaydedildi -> outputs/tables/{name}.csv")


def banner(text: str) -> None:
    print("\n" + "#" * 70)
    print(f"#  {text}")
    print("#" * 70)


def main() -> int:
    banner("YMH340 VERI MADENCILIGI PROJESI  |  AVRUPA FUTBOL MAC SONUCU TAHMINI")
    setup_style()
    config.ensure_directories()

    # ----------------------------------------------------------------- 1) VERI
    raw = data_loading.load_raw_data()
    summary = data_loading.summarize_dataframe(raw)
    save_table(summary, "00_veri_ozeti")

    # Hedef degiskeni ham veri uzerinde de uret (EDA gorselleri icin)
    raw_with_target = preprocessing.add_target(raw)

    # Eksik veri raporu
    missing = preprocessing.missing_report(raw)
    save_table(missing, "01_eksik_veri_raporu")

    # ----------------------------------------------------------- 3) HAZIRLAMA
    # (Modelleme cercevesi EDA korelasyon haritasi icin de gerekli)
    model_df = preprocessing.build_modeling_frame(raw)
    X, y = preprocessing.split_X_y(model_df)

    # Aykiri deger raporu (ham mac istatistikleri uzerinde)
    outliers = preprocessing.detect_outliers_iqr(raw, config.MATCH_STAT_COLS + config.ODDS_COLS)
    save_table(outliers, "02_aykiri_deger_raporu")

    # ----------------------------------------------------------------- 2) EDA
    eda.run_all(raw_with_target, model_df, missing)

    # Tanimlayici istatistikler tablosu
    desc = X.describe().T.round(3).reset_index().rename(columns={"index": "ozellik"})
    save_table(desc, "03_tanimlayici_istatistik")

    # --------------------------------------------------------- 4) OZELLIK SECIMI
    selected, importance = feature_selection.run(X, y)
    save_table(importance.round(4), "04_ozellik_onem_skorlari")

    # --------------------------------------------------------------- 5) MODELLEME
    out = modeling.run(X, y, selected)

    # Sonuc tablolari
    save_table(out["results"], "05_model_sonuclari_tum")
    # Ozet pivot (algoritma x ozellik kumesi -> dogruluk)
    pivot = out["results"].pivot(index="Algoritma", columns="Özellik Kümesi",
                                 values="Doğruluk (Accuracy)")
    pivot["Fark"] = (pivot["Tüm Özellikler"] - pivot["Seçilmiş Özellikler"]).round(4)
    pivot = pivot.sort_values("Tüm Özellikler", ascending=False).reset_index()
    save_table(pivot, "06_dogruluk_pivot")

    # En iyi model: sinif bazli rapor + karmasiklik matrisi
    clf_rep = modeling.classification_report_df(out["y_test"], out["best_pred"])
    save_table(clf_rep.reset_index().rename(columns={"index": "sinif"}),
               "07_siniflandirma_raporu", index=False)

    # --------------------------------------------------------------- 5) GORSELLER
    modeling.plot_accuracy_comparison(out["results"])
    modeling.plot_confusion_matrix(out["y_test"], out["best_pred"], out["best_name"])

    # En iyi modeli diske kaydet
    model_path = config.MODELS_DIR / "en_iyi_model.joblib"
    joblib.dump(out["best_model"], model_path)
    print(f"   [model] kaydedildi -> outputs/models/{model_path.name}")

    # --------------------------------------------------------------------- OZET
    banner("CALISMA TAMAMLANDI - OZET")
    print(f"Modelleme veri seti     : {X.shape[0]:,} mac x {X.shape[1]} ozellik")
    print(f"Cogunluk-sinif tabani   : %{out['baseline']*100:.2f}")
    best = out["res_all"].loc[out["res_all"]["Doğruluk (Accuracy)"].idxmax()]
    print(f"En iyi model (tum oz.)  : {best['Algoritma']} -> "
          f"%{best['Doğruluk (Accuracy)']*100:.2f} dogruluk")
    print(f"Secilen ozellikler (k={config.TOP_K_FEATURES}): {selected}")
    print(f"\nTum gorseller : outputs/figures/")
    print(f"Tum tablolar  : outputs/tables/")
    print(f"En iyi model  : outputs/models/en_iyi_model.joblib")
    print("#" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
