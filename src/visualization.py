"""
visualization.py
================
Tum modullerin ortak kullandigi gorsel yardimci fonksiyonlari.

Burada matplotlib/seaborn icin tutarli bir stil tanimlanir ve figurleri
diske kaydeden tek bir yardimci fonksiyon (`save_fig`) bulunur. Boylece
butun grafikler ayni gorsel dile (font, izgara, cozunurluk) sahip olur.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Ekran olmadan (headless) figur uretimi icin
import matplotlib.pyplot as plt
import seaborn as sns

from . import config


def setup_style() -> None:
    """Proje genelinde tutarli bir grafik stili uygular."""
    sns.set_theme(style="whitegrid", palette=config.PALETTE)
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": config.FIG_DPI,
        "savefig.bbox": "tight",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.edgecolor": "#444444",
        "axes.linewidth": 0.8,
        "figure.titlesize": 15,
        "figure.titleweight": "bold",
        # DejaVu Sans Turkce karakterleri (c,g,i,o,s,u) destekler
        "font.family": "DejaVu Sans",
    })


def save_fig(fig: plt.Figure, name: str, *, tight: bool = True) -> Path:
    """
    Bir figuru standart cozunurlukte FIGURES_DIR altina kaydeder.

    Parameters
    ----------
    fig  : kaydedilecek matplotlib Figure
    name : uzantisiz dosya adi (orn. "01_sinif_dagilimi")
    tight: kenar bosluklarini sikistir

    Returns
    -------
    Olusturulan dosyanin tam yolu.
    """
    config.ensure_directories()
    path = config.FIGURES_DIR / f"{name}.{config.FIG_FORMAT}"
    if tight:
        fig.tight_layout()
    fig.savefig(path, dpi=config.FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   [figur] kaydedildi -> outputs/figures/{path.name}")
    return path
