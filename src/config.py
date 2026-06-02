"""
config.py
=========
Projenin merkezi yapilandirma modulu.

Tum yol (path) tanimlari, sabitler, ozellik listeleri, hedef degisken
eslemesi ve gorsel ayarlari bu dosyada toplanmistir. Boylece diger
modullerde "sihirli sayilar" (magic numbers) ve gomulu yollar bulunmaz;
tum ayarlar tek bir yerden yonetilir.

YMH340 - Veri Madenciligi Donem Projesi
Avrupa Futbol Liglerinde Mac Sonucu Tahmini
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# 1) DIZIN VE DOSYA YOLLARI
# ---------------------------------------------------------------------------
# Bu dosya src/ altinda oldugu icin proje kok dizini bir ust klasordur.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_FILE: Path = PROJECT_ROOT / "data" / "EUROPEAN_FOOTBALL_DATABASE_FULL.csv"

OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"
FIGURES_DIR: Path = OUTPUT_DIR / "figures"
TABLES_DIR: Path = OUTPUT_DIR / "tables"
MODELS_DIR: Path = OUTPUT_DIR / "models"


def ensure_directories() -> None:
    """Cikti klasorlerini (yoksa) olusturur."""
    for directory in (OUTPUT_DIR, FIGURES_DIR, TABLES_DIR, MODELS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 2) MODELLEME SABITLERI
# ---------------------------------------------------------------------------
RANDOM_STATE: int = 42       # Tekrarlanabilirlik (reproducibility) icin sabit tohum
TEST_SIZE: float = 0.20      # Test kumesi orani (%20 test - %80 egitim)
CV_FOLDS: int = 5            # Capraz dogrulama (cross-validation) kat sayisi
TOP_K_FEATURES: int = 10     # Ozellik seciminde tutulacak ozellik sayisi

# ---------------------------------------------------------------------------
# 3) HEDEF DEGISKEN (SINIF) TANIMI
# ---------------------------------------------------------------------------
# Mac sonucu, ev sahibi ve deplasman gol sayilari karsilastirilarak turetilir.
TARGET_COL: str = "result"

# Sinif kodlari ve okunabilir etiketleri (proje onerisindeki kodlama: 1/0/2)
CLASS_LABELS: dict[int, str] = {
    1: "Ev Sahibi Galibiyeti",
    0: "Beraberlik",
    2: "Deplasman Galibiyeti",
}
# Grafiklerde tutarli siralama icin (kisa etiketler)
CLASS_ORDER: list[int] = [1, 0, 2]
CLASS_SHORT: dict[int, str] = {1: "Ev (1)", 0: "Beraberlik (0)", 2: "Deplasman (2)"}

# ---------------------------------------------------------------------------
# 4) HAM VERI SUTUN GRUPLARI
# ---------------------------------------------------------------------------
# Hedefi DOGRUDAN belirleyen sutunlar -> veri sizintisini (data leakage)
# onlemek icin ozellik olarak ASLA kullanilmaz.
LEAKAGE_COLS: list[str] = ["home_goals", "away_goals"]

# Kimlik/meta veri ya da asiri eksik olan, modele alinmayacak sutunlar.
#  - referee            : %84 eksik + yuksek kardinaliteli kimlik
#  - odds_over_25/under : %73 eksik
#  - ht_home/away_goals : ilk yari golleri -> kismi sizinti (final skora dahil)
#  - date/team/season/source : kimlik/meta veri
DROP_COLS: list[str] = [
    "date", "home_team", "away_team", "referee",
    "odds_over_25", "odds_under_25",
    "ht_home_goals", "ht_away_goals",
    "season", "source",
]

# Bahis (iddaa) oranlari - mac oncesi piyasa sinyali
ODDS_COLS: list[str] = ["odds_home", "odds_draw", "odds_away"]

# Mac ici istatistikler - sahadaki ustunluk sinyali
MATCH_STAT_COLS: list[str] = [
    "home_shots", "away_shots",
    "home_shots_target", "away_shots_target",
    "home_corners", "away_corners",
    "home_fouls", "away_fouls",
    "home_yellow", "away_yellow",
    "home_red", "away_red",
]

# Modelleme icin gerekli olan ham sayisal sutunlar (eksiksiz olmasi istenenler)
REQUIRED_FEATURE_COLS: list[str] = ODDS_COLS + MATCH_STAT_COLS

# Veri hazirlama asamasinda turetilecek (engineered) ozellikler
ENGINEERED_COLS: list[str] = [
    "implied_prob_home", "implied_prob_draw", "implied_prob_away",
    "shots_diff", "shots_target_diff", "corners_diff",
]

# Grafiklerde gosterilecek okunabilir Turkce ozellik adlari
FEATURE_LABELS_TR: dict[str, str] = {
    "odds_home": "Oran: Ev Sahibi",
    "odds_draw": "Oran: Beraberlik",
    "odds_away": "Oran: Deplasman",
    "home_shots": "Ev Şut",
    "away_shots": "Deplasman Şut",
    "home_shots_target": "Ev İsabetli Şut",
    "away_shots_target": "Deplasman İsabetli Şut",
    "home_corners": "Ev Korner",
    "away_corners": "Deplasman Korner",
    "home_fouls": "Ev Faul",
    "away_fouls": "Deplasman Faul",
    "home_yellow": "Ev Sarı Kart",
    "away_yellow": "Deplasman Sarı Kart",
    "home_red": "Ev Kırmızı Kart",
    "away_red": "Deplasman Kırmızı Kart",
    "implied_prob_home": "İma Olasılık: Ev",
    "implied_prob_draw": "İma Olasılık: Beraberlik",
    "implied_prob_away": "İma Olasılık: Deplasman",
    "shots_diff": "Şut Farkı (Ev−Dep)",
    "shots_target_diff": "İsabetli Şut Farkı (Ev−Dep)",
    "corners_diff": "Korner Farkı (Ev−Dep)",
    "result": "Maç Sonucu (hedef)",
}


def tr_label(col: str) -> str:
    """Bir sutun adini okunabilir Turkce etikete cevirir (yoksa adi dondurur)."""
    return FEATURE_LABELS_TR.get(col, col)

# ---------------------------------------------------------------------------
# 5) GORSEL AYARLARI
# ---------------------------------------------------------------------------
FIG_DPI: int = 150
FIG_FORMAT: str = "png"

# Tutarli renk paleti (3 sinif icin)
CLASS_COLORS: dict[int, str] = {
    1: "#2E86AB",   # Ev sahibi - mavi
    0: "#F4A261",   # Beraberlik - turuncu
    2: "#E63946",   # Deplasman - kirmizi
}
PRIMARY_COLOR: str = "#2E86AB"
ACCENT_COLOR: str = "#E63946"
PALETTE: list[str] = ["#2E86AB", "#E63946", "#F4A261", "#2A9D8F",
                      "#8E44AD", "#264653", "#E9C46A", "#457B9D"]
