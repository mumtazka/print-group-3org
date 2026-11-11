#!/usr/bin/env python
# coding: utf-8

# # Analisis Risiko Gangguan Pernapasan
# ## Kualitas Udara, Meteorologi, dan Mobilitas Perkotaan di Indonesia
# ### PRINT Group 3org — PRINT 2026
# 
# Semua temuan bersifat **asosiasi statistik**, bukan hubungan sebab-akibat.

import glob, io, os, warnings
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend untuk script
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats
warnings.filterwarnings('ignore')
# Simpan gambar ke figures/ di root repo
_fig_dir = os.path.join(os.path.dirname(os.path.abspath('notebooks/analisis_v2.ipynb')), '..', 'figures')
_fig_dir = os.path.normpath(os.path.join(os.getcwd(), 'figures'))
os.makedirs(_fig_dir, exist_ok=True)


# ## 1. Muat Data & Cek Awal

try:
    from google.colab import files
    import io
    uploaded = files.upload()
    csv_files = [n for n in uploaded if n.lower().endswith('.csv')]
    FILE = csv_files[0]
    df_raw = pd.read_csv(io.BytesIO(uploaded[FILE]))
except ImportError:
    import glob
    candidates = (
        glob.glob('data/*.csv') +
        glob.glob('../data/*.csv') +
        glob.glob('/kaggle/input/**/*.csv', recursive=True) +
        glob.glob('*.csv') +
        glob.glob('../*.csv')
    )
    preferred = [p for p in candidates if 'air_quality_health' in os.path.basename(p)]
    FILE = preferred[0] if preferred else candidates[0]
    df_raw = pd.read_csv(FILE)

df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
print(f"File: {os.path.basename(FILE)}")
print(f"Shape: {df_raw.shape}")
print(f"Duplikat baris: {df_raw.duplicated().sum()}")
print(f"Duplikat record_id: {df_raw['record_id'].duplicated().sum()}")
print(f"Rentang: {df_raw['timestamp'].min().date()} s.d. {df_raw['timestamp'].max().date()}")
print(f"Kota: {sorted(df_raw['city'].unique())}")
df_raw.head()


# ## 2. Cleaning Data
# - Imputasi missing value menggunakan **median per kota** (bukan median global).
# - Outlier IQR dilaporkan namun tidak dibuang. Nilai 0 pada `rainfall_mm` dipertahankan.

df = df_raw.copy()
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 2a. Missing
print("=== Missing per Kolom ===")
print(df.isnull().sum()[df.isnull().sum() > 0])

# 2b. Sebaran missing per kota
cols_impute = ['temperature_c', 'traffic_index', 'pm25_ug_m3']
for col in cols_impute:
    print(f"\n{col}:")
    print(df[df[col].isnull()].groupby('city').size())

# 2c. Imputasi median per kota
for col in cols_impute:
    df[col] = df.groupby('city')[col].transform(lambda x: x.fillna(x.median()))
print("\nVerifikasi setelah imputasi:")
print(df[cols_impute].isnull().sum())

# 2d. Outlier IQR
print("\n=== Outlier IQR (dipertahankan) ===")
for col in ['temperature_c','rainfall_mm','traffic_index','pm25_ug_m3','no2_ppb','aqi_score','respiratory_cases']:
    Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
    n_out = ((df[col] < Q1-1.5*(Q3-Q1)) | (df[col] > Q3+1.5*(Q3-Q1))).sum()
    print(f"  {col}: {n_out} outlier")

# 2e. Crosstab
print("\n=== Crosstab City x Zone ===")
print(pd.crosstab(df['city'], df['zone_type']))
print("Catatan: Setiap kota hanya memiliki satu tipe zona.")


# ## 3. Variabel Turunan

df['risk_aqi']      = df['aqi_score'] > 100
df['hour']          = df['timestamp'].dt.hour
df['is_weekend']    = df['timestamp'].dt.dayofweek >= 5
df['rain_category'] = df['rainfall_mm'] > 0
print(f"risk_aqi: {df['risk_aqi'].sum()} baris ({df['risk_aqi'].mean()*100:.2f}%)")
print(f"Weekend: {df['is_weekend'].sum()} | Weekday: {(~df['is_weekend']).sum()}")
print(f"Hujan: {df['rain_category'].sum()} | Tidak: {(~df['rain_category']).sum()}")


# ## 4. Analisis Spasial

kota_tbl = df.groupby('city').agg(
    AQI=('aqi_score','mean'), PM25=('pm25_ug_m3','mean'),
    NO2=('no2_ppb','mean'),   Kasus=('respiratory_cases','mean')
).round(2).sort_values('AQI', ascending=False)

zona_tbl = df.groupby('zone_type').agg(
    AQI=('aqi_score','mean'), PM25=('pm25_ug_m3','mean'),
    NO2=('no2_ppb','mean'),   Kasus=('respiratory_cases','mean')
).round(2)

print("=== Rerata per Kota ==="); print(kota_tbl)
print("\n=== Rerata per Zona ==="); print(zona_tbl)
print("\n=== Kota Zona Traffic (Jakarta Pusat, Bandung, Medan) ===")
print(kota_tbl.loc[['Jakarta Pusat','Bandung','Medan']])


# ## 5. Analisis Temporal

jam_tbl = df.groupby('hour').agg(
    traffic=('traffic_index','mean'), AQI=('aqi_score','mean'),
    kasus=('respiratory_cases','mean')
).round(2)

def pct_risk(x): return (x > 100).mean() * 100
wd_we = df.groupby('is_weekend').agg(
    traffic=('traffic_index','mean'), PM25=('pm25_ug_m3','mean'),
    NO2=('no2_ppb','mean'), AQI=('aqi_score','mean'),
    kasus=('respiratory_cases','mean'), pct_AQI_risk=('aqi_score', pct_risk)
).round(2)
wd_we.index = ['Weekday','Weekend']
print("=== Rerata per Jam ==="); print(jam_tbl)
print("\n=== Weekday vs Weekend ==="); print(wd_we)


# ## 6. Hujan & Cuaca

hujan_tbl = df.groupby('rain_category').agg(
    PM25=('pm25_ug_m3','mean'), AQI=('aqi_score','mean'), kasus=('respiratory_cases','mean')
).round(2)
hujan_tbl.index = ['Tidak Hujan','Hujan']
print("=== Hujan vs Tidak Hujan ==="); print(hujan_tbl)

rho_rain_pm25, _ = stats.spearmanr(df['rainfall_mm'], df['pm25_ug_m3'])
rho_rain_aqi,  _ = stats.spearmanr(df['rainfall_mm'], df['aqi_score'])
rho_temp_aqi,  _ = stats.spearmanr(df['temperature_c'], df['aqi_score'])
rho_temp_cas,  _ = stats.spearmanr(df['temperature_c'], df['respiratory_cases'])
print(f"rho rainfall-PM2.5={rho_rain_pm25:.3f}  rainfall-AQI={rho_rain_aqi:.3f}")
print(f"rho suhu-AQI={rho_temp_aqi:.3f}  suhu-kasus={rho_temp_cas:.3f}")


# ## 7. Uji Statistik & Korelasi

from scipy import stats as _stats
safe  = df[~df['risk_aqi']]['respiratory_cases']
risky = df[ df['risk_aqi']]['respiratory_cases']
_, mw_p = _stats.mannwhitneyu(safe, risky, alternative='two-sided')
print(f"Mann-Whitney AQI aman vs berisiko: {safe.mean():.2f} vs {risky.mean():.2f}, p={mw_p:.3e}")

groups_zona = [g['respiratory_cases'].values for _,g in df.groupby('zone_type')]
_, kw_p = _stats.kruskal(*groups_zona)
print(f"Kruskal-Wallis antar zona: p={kw_p:.3e}")

wd_cas = df[~df['is_weekend']]['respiratory_cases']
we_cas = df[ df['is_weekend']]['respiratory_cases']
_, p_cas = _stats.mannwhitneyu(wd_cas, we_cas, alternative='two-sided')
_, p_aqi = _stats.mannwhitneyu(df[~df['is_weekend']]['aqi_score'],
                                df[ df['is_weekend']]['aqi_score'], alternative='two-sided')
print(f"Mann-Whitney AQI weekday vs weekend: p={p_aqi:.3e}")
print(f"Mann-Whitney kasus weekday vs weekend: p={p_cas:.3e}")

rho_dict = {}
print("\n=== Spearman vs respiratory_cases ===")
for col in ['aqi_score','no2_ppb','pm25_ug_m3','traffic_index','rainfall_mm','temperature_c']:
    r, p = _stats.spearmanr(df[col], df['respiratory_cases'])
    rho_dict[col] = r
    print(f"  {col:20s}: rho={r:.3f}, p={p:.3e}")
rho_tr_no2, _ = _stats.spearmanr(df['traffic_index'], df['no2_ppb'])
print(f"  traffic vs no2        : rho={rho_tr_no2:.3f}")


# ## 8. Analisis Lag
# Shift AQI dilakukan **di dalam groupby city** agar tidak terjadi lompatan data antar kota.

df_s = df.sort_values(['city','timestamp']).copy()
lag_res = {}
print("=== Lag AQI (per kota) → kasus ===")
for lag in [0,1,2,4]:
    aqi_lag = df_s['aqi_score'] if lag==0 else df_s.groupby('city')['aqi_score'].shift(lag)
    mask = aqi_lag.notna()
    r, p = stats.spearmanr(aqi_lag[mask], df_s.loc[mask,'respiratory_cases'])
    lag_res[lag] = r
    print(f"  Lag {lag} ({lag*3} jam): rho={r:.3f}, n={mask.sum()}, p={p:.3e}")


# ## 9. Visualisasi

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({'font.size':11,'axes.titlesize':12})

# --- gambar_2 ---
kota_s = kota_tbl.sort_values('AQI', ascending=True)
fig, ax = plt.subplots(figsize=(9,6))
y = np.arange(len(kota_s)); h = 0.35
ax.barh(y-h/2, kota_s['AQI'],   h, label='Rerata AQI',              color='#4472C4')
ax.barh(y+h/2, kota_s['Kasus'], h, label='Rerata Kasus Pernapasan', color='#ED7D31')
ax.axvline(100, color='red', linestyle='--', lw=1.4, label='Ambang AQI 100')
ax.set_yticks(y); ax.set_yticklabels(kota_s.index)
ax.set_xlabel('Nilai Rerata'); ax.set_title('Rerata AQI dan Kasus Pernapasan per Kota')
ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.13), ncol=3)
plt.tight_layout(); plt.savefig(os.path.join(_fig_dir, 'gambar_2_antar_kota.png'), dpi=200, bbox_inches='tight'); plt.show()

# --- gambar_3 ---
zona_p = zona_tbl[['AQI','PM25','NO2','Kasus']]
fig, ax = plt.subplots(figsize=(9,5))
y = np.arange(len(zona_p)); bh = 0.18
for i,(col,clr) in enumerate(zip(zona_p.columns,['#4472C4','#ED7D31','#A9D18E','#FF6666'])):
    ax.barh(y+(i-2)*bh+bh/2, zona_p[col], bh, label=col, color=clr)
ax.set_yticks(y); ax.set_yticklabels(zona_p.index)
ax.set_xlabel('Nilai Rerata'); ax.set_title('Profil per Tipe Zona')
ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.13), ncol=4)
plt.tight_layout(); plt.savefig(os.path.join(_fig_dir, 'gambar_3_zona.png'), dpi=200, bbox_inches='tight'); plt.show()

# --- gambar_4 ---
fig, axes = plt.subplots(3,1, figsize=(10,9), sharex=True)
hx = jam_tbl.index
axes[0].plot(hx, jam_tbl['traffic'], marker='o', color='#4472C4')
axes[0].set_ylabel('Traffic Index'); axes[0].set_title('Traffic Index per Jam')
axes[1].plot(hx, jam_tbl['AQI'],    marker='o', color='#ED7D31')
axes[1].set_ylabel('AQI');          axes[1].set_title('AQI per Jam')
axes[2].plot(hx, jam_tbl['kasus'],  marker='o', color='#A9D18E')
axes[2].set_ylabel('Kasus');        axes[2].set_title('Kasus Pernapasan per Jam')
axes[2].set_xlabel('Jam'); axes[2].xaxis.set_major_locator(mticker.MultipleLocator(3))
plt.tight_layout(); plt.savefig(os.path.join(_fig_dir, 'gambar_4_jam.png'), dpi=200, bbox_inches='tight'); plt.show()

# --- gambar_5 ---
fig, axes = plt.subplots(1,3, figsize=(12,5))
for ax, (col, lbl) in zip(axes,[('PM25','PM2.5 (µg/m³)'),('AQI','AQI'),('kasus','Kasus')]):
    vals = hujan_tbl[col]
    bars = ax.bar(hujan_tbl.index, vals, color=['#E07B54','#5B9BD5'])
    for bar,v in zip(bars,vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f'{v:.2f}', ha='center', va='bottom')
    ax.set_title(lbl)
plt.suptitle('Hujan vs Tidak Hujan', y=1.02)
plt.tight_layout(); plt.savefig(os.path.join(_fig_dir, 'gambar_5_hujan.png'), dpi=200, bbox_inches='tight'); plt.show()

# --- gambar_6 ---
rho6_ac, _ = stats.spearmanr(df['aqi_score'],     df['respiratory_cases'])
rho6_tn, _ = stats.spearmanr(df['traffic_index'],  df['no2_ppb'])
fig, axes = plt.subplots(1,2, figsize=(12,5))
axes[0].scatter(df['aqi_score'],    df['respiratory_cases'], alpha=0.15, s=8, color='#4472C4')
axes[0].set_xlabel('AQI'); axes[0].set_ylabel('Kasus')
axes[0].set_title(f'AQI vs Kasus Pernapasan\n(ρ={rho6_ac:.3f})')
axes[1].scatter(df['traffic_index'], df['no2_ppb'], alpha=0.15, s=8, color='#ED7D31')
axes[1].set_xlabel('Traffic Index'); axes[1].set_ylabel('NO₂ (ppb)')
axes[1].set_title(f'Traffic Index vs NO₂\n(ρ={rho6_tn:.3f})')
plt.tight_layout(); plt.savefig(os.path.join(_fig_dir, 'gambar_6_hubungan.png'), dpi=200, bbox_inches='tight'); plt.show()

# --- gambar_7 ---
fig, ax = plt.subplots(figsize=(9,5))
x = np.arange(3); w = 0.3
v_wd = [wd_we.loc['Weekday',m] for m in ['traffic','AQI','kasus']]
v_we = [wd_we.loc['Weekend',m] for m in ['traffic','AQI','kasus']]
b1 = ax.bar(x-w/2, v_wd, w, label='Weekday', color='#4472C4')
b2 = ax.bar(x+w/2, v_we, w, label='Weekend', color='#ED7D31')
for bar in list(b1)+list(b2):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3, f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(['Traffic Index','AQI','Kasus Pernapasan'])
ax.set_title('Weekday vs Weekend')
ax.legend(loc='upper center', bbox_to_anchor=(0.5,-0.12), ncol=2)
plt.tight_layout(); plt.savefig(os.path.join(_fig_dir, 'gambar_7_weekday_weekend.png'), dpi=200, bbox_inches='tight'); plt.show()
print("Semua gambar tersimpan di figures/")


# ## 10. Ringkasan Angka & Assert
# Semua nilai dicocokkan dengan nilai acuan proposal (toleransi 0,01; korelasi 0,001).

from scipy import stats as _st2
TOL = 0.01; TOL_R = 0.001
failures = []

def chk(label, actual, expected, tol=TOL):
    diff = abs(actual - expected)
    ok = diff <= tol
    tag = "LOLOS" if ok else "GAGAL"
    if not ok: failures.append((label, actual, expected, diff))
    print(f"[{tag}] {label}: {actual:.4f}  acuan={expected}  Δ={diff:.4f}")

pct_rv = df["risk_aqi"].mean()*100
n_rv   = int(df["risk_aqi"].sum())
safe_m  = df[~df["risk_aqi"]]["respiratory_cases"].mean()
risky_m = df[ df["risk_aqi"]]["respiratory_cases"].mean()

chk("% AQI>100",         pct_rv, 21.42)
chk("n AQI>100",         n_rv,   1071, tol=0)
chk("kasus AQI aman",    safe_m, 52.82)
chk("kasus AQI berisiko",risky_m,79.91)
chk("n Moderate",(df["air_quality_status"]=="Moderate").sum(),3639,tol=0)
chk("n USG",     (df["air_quality_status"]=="Unhealthy for Sensitive Groups").sum(),1071,tol=0)
chk("n Good",    (df["air_quality_status"]=="Good").sum(),290,tol=0)
chk("Jakarta Pusat AQI",  kota_tbl.loc["Jakarta Pusat","AQI"],  97.23)
chk("Jakarta Pusat kasus",kota_tbl.loc["Jakarta Pusat","Kasus"],83.02)
chk("Makassar AQI",       kota_tbl.loc["Makassar","AQI"],       62.39)
chk("Makassar kasus",     kota_tbl.loc["Makassar","Kasus"],     35.02)
chk("Bekasi PM2.5",       kota_tbl.loc["Bekasi","PM25"],        68.26)
chk("Tangerang PM2.5",    kota_tbl.loc["Tangerang","PM25"],     64.30)
chk("Bandung AQI",        kota_tbl.loc["Bandung","AQI"],        91.63)
chk("Bandung kasus",      kota_tbl.loc["Bandung","Kasus"],      71.39)
chk("Medan AQI",          kota_tbl.loc["Medan","AQI"],          90.22)
chk("Medan kasus",        kota_tbl.loc["Medan","Kasus"],        59.77)
chk("Zona Traffic NO2",      zona_tbl.loc["Traffic","NO2"],       73.03)
chk("Zona Traffic AQI",      zona_tbl.loc["Traffic","AQI"],       93.03)
chk("Zona Traffic kasus",    zona_tbl.loc["Traffic","Kasus"],     71.39)
chk("Zona Industrial PM2.5", zona_tbl.loc["Industrial","PM25"],   62.54)
chk("Zona Residential AQI",  zona_tbl.loc["Residential","AQI"],   70.00)
chk("Zona Residential kasus",zona_tbl.loc["Residential","Kasus"], 41.98)
chk("Jam 06 traffic",jam_tbl.loc[6,"traffic"],  65.57)
chk("Jam 09 traffic",jam_tbl.loc[9,"traffic"],  65.70)
chk("Jam 18 traffic",jam_tbl.loc[18,"traffic"], 64.91)
chk("Jam 06 AQI",   jam_tbl.loc[6,"AQI"],       91.08)
chk("Jam 09 AQI",   jam_tbl.loc[9,"AQI"],       91.09)
chk("Jam 18 AQI",   jam_tbl.loc[18,"AQI"],      90.82)
chk("Jam 06 kasus", jam_tbl.loc[6,"kasus"],     63.07)
chk("Jam 18 kasus", jam_tbl.loc[18,"kasus"],    63.30)
chk("Jam 21 AQI",   jam_tbl.loc[21,"AQI"],      80.07)
chk("Hujan PM2.5 kering",hujan_tbl.loc["Tidak Hujan","PM25"],60.54)
chk("Hujan PM2.5 basah", hujan_tbl.loc["Hujan","PM25"],      44.61)
chk("Hujan AQI kering",  hujan_tbl.loc["Tidak Hujan","AQI"], 87.69)
chk("Hujan AQI basah",   hujan_tbl.loc["Hujan","AQI"],       65.30)
chk("Hujan kasus kering",hujan_tbl.loc["Tidak Hujan","kasus"],60.75)
chk("Hujan kasus basah", hujan_tbl.loc["Hujan","kasus"],      48.52)
chk("rho rainfall-PM2.5",rho_rain_pm25,-0.405,tol=TOL_R)
chk("rho rainfall-AQI",  rho_rain_aqi, -0.413,tol=TOL_R)
chk("rho AQI-kasus",    rho_dict["aqi_score"],    0.811,tol=TOL_R)
chk("rho NO2-kasus",    rho_dict["no2_ppb"],      0.779,tol=TOL_R)
chk("rho PM2.5-kasus",  rho_dict["pm25_ug_m3"],   0.719,tol=TOL_R)
chk("rho traffic-kasus",rho_dict["traffic_index"],0.464,tol=TOL_R)
chk("rho traffic-NO2",  rho_tr_no2,               0.662,tol=TOL_R)
chk("rho suhu-AQI",    rho_temp_aqi, -0.02, tol=0.005)
chk("rho suhu-kasus",  rho_temp_cas, -0.10, tol=0.005)
chk("Weekday traffic",wd_we.loc["Weekday","traffic"],60.20)
chk("Weekend traffic",wd_we.loc["Weekend","traffic"],35.88)
chk("Weekday PM2.5",  wd_we.loc["Weekday","PM25"],  60.22)
chk("Weekend PM2.5",  wd_we.loc["Weekend","PM25"],  51.71)
chk("Weekday NO2",    wd_we.loc["Weekday","NO2"],   65.53)
chk("Weekend NO2",    wd_we.loc["Weekend","NO2"],   52.08)
chk("Weekday AQI",    wd_we.loc["Weekday","AQI"],   87.85)
chk("Weekend AQI",    wd_we.loc["Weekend","AQI"],   73.79)
chk("Weekday kasus",  wd_we.loc["Weekday","kasus"], 60.79)
chk("Weekend kasus",  wd_we.loc["Weekend","kasus"], 53.27)
chk("Weekday %AQI>100",wd_we.loc["Weekday","pct_AQI_risk"],28.43)
chk("Weekend %AQI>100",wd_we.loc["Weekend","pct_AQI_risk"], 4.10)
chk("Lag 0",lag_res[0],0.811,tol=TOL_R)
chk("Lag 1",lag_res[1],0.422,tol=TOL_R)
chk("Lag 2",lag_res[2],0.384,tol=TOL_R)
chk("Lag 4",lag_res[4],0.428,tol=TOL_R)

print()
if failures:
    print(f"TOTAL GAGAL: {len(failures)}")
    for lbl,act,exp,d in failures:
        print(f"  ⚠ {lbl}: aktual={act:.4f}  acuan={exp}  Δ={d:.4f}")
else:
    print("SEMUA ASSERT LOLOS ✓")

