# Analisis Risiko Gangguan Pernapasan Berdasarkan Kualitas Udara, Meteorologi, dan Mobilitas Perkotaan di Indonesia

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mumtazka/print-group-3org/blob/main/notebooks/analisis_v2.ipynb)

**PRINT Group 3org** — PRINT 2026
- Ravi Rinakit Kurniawan (24060126140167)
- Meilan Malik Lutfi Prasetyo (24060126140154)
- Mumtaz Kholafiyan Alfan (24060126130062)

Repositori ini memuat kode analisis cleaning, EDA, dan uji statistik pada dataset kualitas udara dan gangguan pernapasan di 10 kota Indonesia (5.000 catatan, interval 3 jam, 25 Agustus – 26 Oktober 2026). Proposal lengkap dikumpulkan terpisah melalui form panitia.

---

## Struktur Folder

```
print/
├── data/
│   └── indonesia_air_quality_health.csv   # Dataset kompetisi
├── notebooks/
│   └── analisis_v2.ipynb                  # Notebook utama (cleaning → EDA → uji → lag → assert)
├── src/
│   └── analisis_v2.py                     # Script Python setara notebook
├── figures/
│   ├── gambar_2_antar_kota.png
│   ├── gambar_3_zona.png
│   ├── gambar_4_jam.png
│   ├── gambar_5_hujan.png
│   ├── gambar_6_hubungan.png
│   └── gambar_7_weekday_weekend.png
├── requirements.txt
└── README.md
```

---

## Cara Menjalankan

```bash
# 1. Install dependensi
pip install -r requirements.txt

# 2. Pastikan dataset ada di:
#    data/indonesia_air_quality_health.csv

# 3a. Jalankan notebook (dari root repo)
jupyter notebook notebooks/analisis_v2.ipynb

# 3b. Atau jalankan script langsung
python src/analisis_v2.py
```

Gambar hasil analisis tersimpan otomatis ke folder `figures/`.
