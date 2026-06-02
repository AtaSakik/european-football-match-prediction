"""
YMH340 Veri Madenciligi Donem Projesi
=====================================
Avrupa Futbol Liglerinde Mac Sonucu Tahmini (sinif siniflandirma).

Bu paket, ham CSV'den nihai model karsilastirmasina kadar uzanan veri
madenciligi hattini moduller halinde icerir:

    config              -> yapilandirma, yollar, sabitler
    data_loading        -> veri okuma ve ozetleme
    preprocessing       -> hedef turetme, temizleme, ozellik muhendisligi
    eda                 -> kesifsel veri analizi gorselleri
    feature_selection   -> ozellik secimi (ANOVA F + Random Forest)
    modeling            -> model egitimi ve karsilastirmali degerlendirme
    visualization       -> ortak grafik yardimcilari
"""

__version__ = "1.0.0"
