import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

dateiname = "clt_f107_nf_final.txt"

# 1. Datei zeilenweise einlesen
zeilen = []
with open(dateiname, "r", encoding="latin1") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        teile = line.split(":")
        if len(teile) >= 4:
            datum = teile.pop(0).strip()
            stunde = teile.pop(0).strip()
            _ = teile.pop(0)
            wert = teile.pop(0).strip()
            zeilen.append({"date": datum, "hour": stunde, "sfu": wert})

df = pd.DataFrame(zeilen)
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
df["sfu"] = pd.to_numeric(df["sfu"], errors="coerce")
df = df.dropna(subset=["date", "sfu"])

# Tageswerte bilden (bevorzugt 12 Uhr UTC Noonflux, sonst Tagesmittel)
df_noon = df[df["hour"] == 12].groupby("date", as_index=False)["sfu"].mean()
df_all = df.groupby("date", as_index=False)["sfu"].mean()
df_daily = pd.merge(df_all, df_noon, on="date", how="left", suffixes=("_all", "_noon"))
df_daily["sfu"] = df_daily["sfu_noon"].fillna(df_daily["sfu_all"])
df_daily = df_daily[["date", "sfu"]].sort_values("date").reset_index(drop=True)

letztes_datum = df_daily["date"].max()

# ==============================================================================
# DIAGRAMM 1: Letzte 30 Tage
# ==============================================================================
start_30 = letztes_datum - pd.Timedelta(days=29)
df_30 = df_daily[df_daily["date"] >= start_30]

fig1, ax = plt.subplots(figsize=(10, 5), dpi=150)
ax.plot(df_30["date"], df_30["sfu"], marker="o", linestyle="-", linewidth=2, markersize=5, color="#1f77b4")
ax.set_title(
    f"Solar Flux Index (F10.7) – Letzte 30 Tage (Stand: {letztes_datum.strftime('%d.%m.%Y')})",
    fontsize=13, fontweight="bold", pad=12
)
ax.set_xlabel("Datum (UTC)", fontsize=10)
ax.set_ylabel("Solar Flux Density [sfu]", fontsize=10)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m."))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
plt.xticks(rotation=45)
ax.grid(True, linestyle="--", alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("sfu_30tage.png")
plt.close(fig1)

# ==============================================================================
# DIAGRAMM 2: Gesamtauswertung ab 01.01.2024
# ==============================================================================
df_2024 = df_daily[df_daily["date"] >= "2024-01-01"].copy().reset_index(drop=True)
df_2024["ma27"] = df_2024["sfu"].rolling(window=27, min_periods=10).mean()
df_2024["ma81"] = df_2024["sfu"].rolling(window=81, min_periods=20).mean()

fig2 = plt.figure(figsize=(13, 8.5), dpi=160)
gs = fig2.add_gridspec(2, 2, height_ratios=[1.25, 1], hspace=0.42, wspace=0.22)

# --- Oben: Zeitverlauf + 27d / 81d Mittel ---
ax_top = fig2.add_subplot(gs[0, :])
ax_top.plot(df_2024["date"], df_2024["sfu"], color="#9ecae1", linewidth=0.9, label="Tagesmittel (Mittagsfluss)")
ax_top.plot(df_2024["date"], df_2024["ma27"], color="#1f4e78", linewidth=1.6, label="27-Tage-Mittel (1 Sonnenrotation)")
ax_top.plot(df_2024["date"], df_2024["ma81"], color="#8b0000", linewidth=1.8, label="81-Tage-Mittel (F10.7A Index)")

# Max & Min annotieren
idx_max = df_2024["sfu"].idxmax()
idx_min = df_2024["sfu"].idxmin()
row_max = df_2024.loc[idx_max]
row_min = df_2024.loc[idx_min]

ax_top.scatter(row_max["date"], row_max["sfu"], color="#d62728", zorder=5, s=35)
ax_top.annotate(
    f"Max: {row_max['sfu']:.1f} sfu\n({row_max['date'].strftime('%d.%m.%Y')})",
    xy=(row_max["date"], row_max["sfu"]),
    xytext=(15, -5), textcoords="offset points",
    fontsize=8.5, color="#8b0000",
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d62728", alpha=0.9),
    arrowprops=dict(arrowstyle="->", color="#d62728", lw=0.8)
)

ax_top.scatter(row_min["date"], row_min["sfu"], color="#1f77b4", zorder=5, s=35)
ax_top.annotate(
    f"Min: {row_min['sfu']:.1f} sfu\n({row_min['date'].strftime('%d.%m.%Y')})",
    xy=(row_min["date"], row_min["sfu"]),
    xytext=(-95, -22), textcoords="offset points",
    fontsize=8.5, color="#1f4e78",
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#1f77b4", alpha=0.9),
    arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=0.8)
)

ax_top.set_title(
    f"Solarer Radiofluss F10.7 (2800 MHz) – Observatorium Wettzell (01.01.2024 – {letztes_datum.strftime('%d.%m.%Y')})",
    fontsize=12.5, fontweight="bold", pad=12
)
ax_top.set_ylabel("Flussdichte [sfu]", fontsize=9.5)
ax_top.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax_top.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax_top.tick_params(axis="x", rotation=30, labelsize=8.5)
ax_top.grid(True, linestyle="--", alpha=0.35)
ax_top.spines["top"].set_visible(False)
ax_top.spines["right"].set_visible(False)
ax_top.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

# --- Unten links: Monatliche Durchschnittswerte ---
ax_bl = fig2.add_subplot(gs[1, 0])
df_2024["year"] = df_2024["date"].dt.year
df_2024["ym"] = df_2024["date"].dt.to_period("M")
monthly = df_2024.groupby(["year", "ym"], as_index=False)["sfu"].mean().sort_values("ym")

jahre = sorted(df_2024["year"].unique())
farben = ["#2b5c8f", "#5b9bd5", "#8ab8e6", "#b4d2f0"]

for idx, jahr in enumerate(jahre):
    sub = monthly[monthly["year"] == jahr]
    jahresmittel = df_2024[df_2024["year"] == jahr]["sfu"].mean()
    farbe = farben[idx % len(farben)]
    ax_bl.bar(
        sub["ym"].astype(str), sub["sfu"], color=farbe, width=0.72,
        label=f"{jahr} (Ø {jahresmittel:.1f} sfu)".replace(".", ",")
    )

tick_pos = list(range(0, len(monthly), 4))
tick_lbl = [monthly["ym"].iloc[i].strftime("%m/%y") for i in tick_pos]
ax_bl.set_xticks(tick_pos)
ax_bl.set_xticklabels(tick_lbl, rotation=35, fontsize=8.5)
ax_bl.set_title(f"Monatliche Durchschnittswerte (2024 – {jahre[-1]})", fontsize=10.5, fontweight="bold", pad=10)
ax_bl.set_ylabel("Mittlerer F10.7 [sfu]", fontsize=9.5)
ax_bl.grid(axis="y", linestyle="--", alpha=0.35)
ax_bl.spines["top"].set_visible(False)
ax_bl.spines["right"].set_visible(False)
ax_bl.legend(loc="upper right", fontsize=8, framealpha=0.9)

# --- Unten rechts: Boxplot nach Jahren ---
ax_br = fig2.add_subplot(gs[1, 1])
daten_jahre = [df_2024[df_2024["year"] == j]["sfu"].values for j in jahre]
labels_jahre = [f"{j}\n(n={len(d)})" for j, d in zip(jahre, daten_jahre)]

bp = ax_br.boxplot(
    daten_jahre, tick_labels=labels_jahre, patch_artist=True, widths=0.38,
    medianprops=dict(color="#8b0000", linewidth=1.8),
    flierprops=dict(marker="o", markersize=3.5, markeredgecolor="#666666", alpha=0.7)
)

for idx, patch in enumerate(bp["boxes"]):
    patch.set_facecolor("#dbe9f6")
    patch.set_edgecolor("#4a6fe3")

mittelwerte = [np.mean(d) for d in daten_jahre]
ax_br.scatter(range(1, len(jahre) + 1), mittelwerte, marker="D", color="#1f4e78", zorder=5, s=35, label="Jahresmittelwert")

for idx, mw in enumerate(mittelwerte):
    ax_br.text(idx + 1.23, mw, f"{mw:.1f}".replace(".", ","), va="center", fontsize=8.5, color="#1f4e78")

ax_br.set_title("Verteilung der Tagesmittel nach Jahren", fontsize=10.5, fontweight="bold", pad=10)
ax_br.set_ylabel("Flussdichte [sfu]", fontsize=9.5)
ax_br.grid(axis="y", linestyle="--", alpha=0.35)
ax_br.spines["top"].set_visible(False)
ax_br.spines["right"].set_visible(False)
ax_br.legend(loc="upper right", fontsize=8, framealpha=0.9)

fig2.text(
    0.04, 0.015,
    "Quelle: Bundesamt für Kartographie und Geodäsie (BKG) – Geodätisches Observatorium Wettzell (WESIS F10.7 Final Noonflux)",
    fontsize=8, color="#555555"
)

plt.savefig("sfu_gesamt_auswertung.png", bbox_inches="tight")
plt.close(fig2)
print("Beide Diagramme wurden erfolgreich erstellt!")

# ==============================================================================
# DIAGRAMM 3: Historische Sonnenzyklen seit 1947 (Ottawa / Penticton)
# ==============================================================================
import urllib.request

hist_rows = []

# 1. Historische Tageswerte 1947 - 2018 von NOAA NCEI laden
url_noaa = (
    "https://noaa.gov"
    "solar-features/solar-radio/noontime-flux/penticton/"
    "penticton_adjusted/listings/"
    "listing_drao_noontime-flux-adjusted_daily.txt"
)

try:
    req = urllib.request.Request(url_noaa, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        for raw_line in resp.read().decode("latin1").splitlines():
            parts = raw_line.strip().split()
            if len(parts) >= 4 and parts[0].isdigit() and len(parts[0]) == 4:
                y, m, d, val = parts[0], parts[1], parts[2], parts[3]
                try:
                    sfu_val = float(val)
                    if 50 < sfu_val < 600:
                        hist_rows.append({"date": f"{y}-{m.zfill(2)}-{d.zfill(2)}", "sfu": sfu_val})
                except ValueError:
                    pass
except Exception as e:
    print("Hinweis NOAA-Archiv:", e)

# 2. Aktuelle Werte ab 2004 von Space Weather Canada laden
url_canada = (
    "https://spaceweather.gc.ca"
    "solar_flux_data/daily_flux_values/fluxtable.txt"
)

try:
    req2 = urllib.request.Request(url_canada, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req2, timeout=25) as resp2:
        for line in resp2.read().decode("latin1").splitlines():
            parts = line.strip().split()
            if len(parts) >= 6 and parts[0].isdigit() and len(parts[0]) == 8:
                d_str = parts[0]
                datum_fmt = f"{d_str[:4]}-{d_str[4:6]}-{d_str[6:8]}"
                try:
                    sfu_val = float(parts[5])
                    if 50 < sfu_val < 600:
                        hist_rows.append({"date": datum_fmt, "sfu": sfu_val})
                except ValueError:
                    pass
except Exception as e:
    print("Hinweis SpaceWeather Canada:", e)

# 3. Deine eigenen Wettzell-Tageswerte (df_daily) als aktuellste Daten anhängen
df_wettzell_hist = df_daily[["date", "sfu"]].copy()
df_wettzell_hist["date"] = df_wettzell_hist["date"].dt.strftime("%Y-%m-%d")

df_all_hist = pd.concat([pd.DataFrame(hist_rows), df_wettzell_hist], ignore_index=True)
df_all_hist["date"] = pd.to_datetime(df_all_hist["date"], errors="coerce")
df_all_hist = df_all_hist.dropna(subset=["date", "sfu"])

print(f"Historische Gesamtdaten: {len(df_all_hist)} Einträge von {df_all_hist['date'].min()} bis {df_all_hist['date'].max()}")

# Tagesmittel und Glättung berechnen
df_h_daily = df_all_hist.groupby("date", as_index=False)["sfu"].mean().sort_values("date").reset_index(drop=True)
df_h_daily["ma81"] = df_h_daily["sfu"].rolling(window=81, min_periods=30, center=True).mean()
df_h_daily["ma365"] = df_h_daily["sfu"].rolling(window=365, min_periods=150, center=True).mean()

fig3, ax3 = plt.subplots(figsize=(13, 5.5), dpi=160)

ax3.plot(df_h_daily["date"], df_h_daily["ma81"], color="#7fb3d5", linewidth=0.9, label="81-Tage-Mittel (F10.7A)")
ax3.plot(df_h_daily["date"], df_h_daily["ma365"], color="#1f4e78", linewidth=2.0, label="365-Tage-Mittel (Zyklusverlauf)")

zyklen = [
    ("Zyklus 18", "1947-11-01", 255),
    ("Zyklus 19\n(Rekord)", "1958-03-01", 285),
    ("Zyklus 20", "1968-11-01", 180),
    ("Zyklus 21", "1979-12-01", 230),
    ("Zyklus 22", "1989-11-01", 235),
    ("Zyklus 23", "2000-07-01", 205),
    ("Zyklus 24", "2014-04-01", 165),
    ("Zyklus 25", "2024-10-01", 215),
]

for name, datum_str, y_pos in zyklen:
    ax3.text(
        pd.to_datetime(datum_str), y_pos, name,
        ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#8b0000",
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#d0d0d0", alpha=0.85)
    )

letztes_hist = df_h_daily["date"].max()
ax3.set_title(
    f"Historischer Solarer Radiofluss F10.7 (1947 – {letztes_hist.strftime('%Y')}): Sonnenzyklen 18 bis 25",
    fontsize=12.5, fontweight="bold", pad=12
)
ax3.set_ylabel("Adjusted Solar Flux [sfu]", fontsize=10)
ax3.set_ylim(55, 325)
ax3.xaxis.set_major_locator(mdates.YearLocator(5))
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax3.grid(True, linestyle="--", alpha=0.35)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.legend(loc="upper right", fontsize=9, framealpha=0.9)

fig3.text(
    0.01, 0.01,
    "Quellen: NOAA NCEI / DRAO Ottawa & Penticton (1947–heute) & BKG Observatorium Wettzell – Adjusted F10.7 Flux",
    fontsize=8, color="#555555"
)

plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig("sfu_zyklen_1947.png")
plt.close(fig3)
print("Historisches Zyklus-Diagramm erstellt!")
