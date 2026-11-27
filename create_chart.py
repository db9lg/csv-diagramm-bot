import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from zoneinfo import ZoneInfo

# 1. Wettzell-Daten einlesen
zeilen = []
with open("clt_f107_nf_final.txt", "r", encoding="latin1") as f:
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

df_noon = df[df["hour"] == 12].groupby("date", as_index=False)["sfu"].mean()
df_all = df.groupby("date", as_index=False)["sfu"].mean()
df_daily = pd.merge(df_all, df_noon, on="date", how="left", suffixes=("_all", "_noon"))
df_daily["sfu"] = df_daily["sfu_noon"].fillna(df_daily["sfu_all"])
df_daily = df_daily[["date", "sfu"]].sort_values("date").reset_index(drop=True)

letztes_datum = df_daily["date"].max()
aktueller_sfu = float(df_daily.loc[df_daily["date"] == letztes_datum, "sfu"].mean())

# DIAGRAMM 1: Letzte 30 Tage (Wettzell F10.7)
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

# DIAGRAMM 2: Gesamtauswertung ab 01.01.2024
df_2024 = df_daily[df_daily["date"] >= "2024-01-01"].copy().reset_index(drop=True)
df_2024["ma27"] = df_2024["sfu"].rolling(window=27, min_periods=10).mean()
df_2024["ma81"] = df_2024["sfu"].rolling(window=81, min_periods=20).mean()

fig2 = plt.figure(figsize=(13, 8.5), dpi=160)
gs = fig2.add_gridspec(2, 2, height_ratios=[1.25, 1], hspace=0.42, wspace=0.22)

ax_top = plt.subplot2grid((2, 2), (0, 0), colspan=2, fig=fig2)
ax_top.plot(df_2024["date"], df_2024["sfu"], color="#9ecae1", linewidth=0.9, label="Tagesmittel (Mittagsfluss)")
ax_top.plot(df_2024["date"], df_2024["ma27"], color="#1f4e78", linewidth=1.6, label="27-Tage-Mittel (1 Sonnenrotation)")
ax_top.plot(df_2024["date"], df_2024["ma81"], color="#8b0000", linewidth=1.8, label="81-Tage-Mittel (F10.7A Index)")

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

ax_bl = plt.subplot2grid((2, 2), (1, 0), fig=fig2)
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
ax_bl.set_title(f"Monatliche Durchschnittswerte (2024 – {max(jahre)})", fontsize=10.5, fontweight="bold", pad=10)
ax_bl.set_ylabel("Mittlerer F10.7 [sfu]", fontsize=9.5)
ax_bl.grid(axis="y", linestyle="--", alpha=0.35)
ax_bl.spines["top"].set_visible(False)
ax_bl.spines["right"].set_visible(False)
ax_bl.legend(loc="upper right", fontsize=8, framealpha=0.9)

ax_br = plt.subplot2grid((2, 2), (1, 1), fig=fig2)
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
# 2. GFZ-Daten einlesen (F10.7 seit 1947 + Ap-Index + Sonnenfleckenzahl SN)
gfz_rows = []
with open("gfz_since_1932.txt", "r", encoding="latin1") as f:
    for raw_line in f:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        teile = line.split()
        if len(teile) >= 27:
            y_str = teile.pop(0)
            m_str = teile.pop(0)
            d_str = teile.pop(0)
            if y_str.isdigit() and int(y_str) >= 1947:
                for _ in range(20):
                    teile.pop(0)
                ap_str = teile.pop(0)
                sn_str = teile.pop(0)
                _ = teile.pop(0)
                sfu_str = teile.pop(0)
                try:
                    gfz_rows.append({
                        "date": f"{y_str}-{m_str.zfill(2)}-{d_str.zfill(2)}",
                        "ap": float(ap_str),
                        "sn": float(sn_str),
                        "sfu": float(sfu_str)
                    })
                except ValueError:
                    pass

df_gfz = pd.DataFrame(gfz_rows)
df_gfz["date"] = pd.to_datetime(df_gfz["date"], errors="coerce")
df_gfz = df_gfz.dropna(subset=["date"])

# DIAGRAMM 3: Historische Sonnenzyklen seit 1947
df_hist_sfu = df_gfz[(df_gfz["sfu"] > 50) & (df_gfz["sfu"] < 600)][["date", "sfu"]].copy()
df_all_hist = pd.concat([df_hist_sfu, df_daily[["date", "sfu"]]], ignore_index=True)

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
    "Quellen: GFZ Helmholtz-Zentrum Potsdam / DRAO Ottawa & Penticton (1947–heute) & BKG Observatorium Wettzell – Adjusted F10.7 Flux",
    fontsize=8, color="#555555"
)

plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig("sfu_zyklen_1947.png")
plt.close(fig3)

# DIAGRAMM 4: Weltraumwetter der letzten 30 Tage (Sonnenflecken SN & Ap-Index)
df_gfz_valid = df_gfz[(df_gfz["sn"] >= 0) & (df_gfz["ap"] >= 0)].sort_values("date")
letztes_gfz = df_gfz_valid["date"].max()
df_gfz_30 = df_gfz_valid[df_gfz_valid["date"] >= (letztes_gfz - pd.Timedelta(days=29))].copy()

aktueller_sn = int(df_gfz_30["sn"].tail(1).mean())
aktueller_ap = int(df_gfz_30["ap"].tail(1).mean())

fig4, (ax_sn, ax_ap) = plt.subplots(2, 1, figsize=(11, 7), dpi=150, sharex=True)

ax_sn.plot(df_gfz_30["date"], df_gfz_30["sn"], marker="o", color="#d95f02", linewidth=2, markersize=4.5)
ax_sn.fill_between(df_gfz_30["date"], df_gfz_30["sn"], color="#d95f02", alpha=0.12)
ax_sn.set_title(
    f"Weltraumwetter (Letzte 30 Tage bis {letztes_gfz.strftime('%d.%m.%Y')}): Sonnenfleckenzahl (SN) & Geomagnetischer Ap-Index",
    fontsize=12, fontweight="bold", pad=12
)
ax_sn.set_ylabel("Sonnenfleckenzahl [SN]", fontsize=10)
ax_sn.grid(True, linestyle="--", alpha=0.4)
ax_sn.spines["top"].set_visible(False)
ax_sn.spines["right"].set_visible(False)

ap_farben = ["#2ca02c" if v < 15 else ("#ff7f0e" if v < 30 else "#d62728") for v in df_gfz_30["ap"]]
ax_ap.bar(df_gfz_30["date"], df_gfz_30["ap"], color=ap_farben, width=0.68)
ax_ap.axhline(15, color="#ff7f0e", linestyle="--", linewidth=1, label="Unruhig (Ap ≥ 15 / Kp ≈ 3–4)")
ax_ap.axhline(30, color="#d62728", linestyle="--", linewidth=1, label="Geomagnetischer Sturm (Ap ≥ 30 / Kp ≥ 5)")
ax_ap.set_ylabel("Tages-Ap-Index", fontsize=10)
ax_ap.set_xlabel("Datum (UTC)", fontsize=10)
ax_ap.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m."))
ax_ap.xaxis.set_major_locator(mdates.DayLocator(interval=3))
plt.xticks(rotation=45)
ax_ap.grid(axis="y", linestyle="--", alpha=0.4)
ax_ap.spines["top"].set_visible(False)
ax_ap.spines["right"].set_visible(False)
ax_ap.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

fig4.text(
    0.01, 0.01,
    "Quelle: GFZ Helmholtz-Zentrum Potsdam (Kp / Ap & SILSO Sunspot Number SN)",
    fontsize=8, color="#555555"
)

plt.tight_layout(rect=[0, 0.03, 1, 1])
plt.savefig("weltraumwetter_30tage.png")
plt.close(fig4)

# 3. index.html mit Zeitstempel & Tageswerten erzeugen
jetzt_de = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y um %H:%M Uhr (%Z)")

html_inhalt = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Solar Flux &amp; Weltraumwetter – Observatorium Wettzell &amp; GFZ Potsdam</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      max-width: 1120px;
      margin: 2rem auto;
      padding: 0 1rem;
      color: #222;
      background-color: #f8f9fa;
    }}
    h1 {{
      font-size: 1.65rem;
      color: #1f4e78;
      margin-bottom: 0.3rem;
    }}
    p.subtitle {{
      color: #555;
      margin-top: 0;
      margin-bottom: 1.2rem;
    }}
    .status-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      background: #eef4fa;
      border-left: 4px solid #1f4e78;
      padding: 0.9rem 1.2rem;
      border-radius: 6px;
      margin-bottom: 2rem;
      font-size: 0.95rem;
    }}
    .status-item {{
      margin-right: 1.5rem;
    }}
    .card {{
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 1.2rem;
      margin-bottom: 2rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }}
    .card img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
    }}
    footer {{
      font-size: 0.85rem;
      color: #666;
      text-align: center;
      margin-top: 2rem;
    }}
  </style>
</head>
<body>
  <h1>Solarer Radiofluss F10.7 &amp; Weltraumwetter</h1>
  <p class="subtitle">Automatisch aktualisierte Auswertung – Geodätisches Observatorium Wettzell (BKG) &amp; GFZ Potsdam</p>

  <div class="status-bar">
    <div class="status-item"><strong>Letzte Aktualisierung:</strong> {jetzt_de}</div>
    <div class="status-item"><strong>Aktueller F10.7 ({letztes_datum.strftime('%d.%m.')}):</strong> {aktueller_sfu:.1f} sfu</div>
    <div class="status-item"><strong>Sonnenflecken (SN):</strong> {aktueller_sn}</div>
    <div class="status-item"><strong>Ap-Index:</strong> {aktueller_ap}</div>
  </div>

  <div class="card">
    <img src="sfu_30tage.png" alt="Solar Flux F10.7 der letzten 30 Tage">
  </div>

  <div class="card">
    <img src="weltraumwetter_30tage.png" alt="Sonnenfleckenzahl und Geomagnetischer Ap-Index der letzten 30 Tage">
  </div>

  <div class="card">
    <img src="sfu_gesamt_auswertung.png" alt="Solar Flux F10.7 Gesamtauswertung seit 01.01.2024">
  </div>

  <div class="card">
    <img src="sfu_zyklen_1947.png" alt="Historischer Solar Flux F10.7 seit 1947 – Sonnenzyklen 18 bis 25">
  </div>

  <footer>
    Quellen: Bundesamt für Kartographie und Geodäsie (BKG Wettzell) &amp; GFZ Helmholtz-Zentrum Potsdam | Aktualisierung täglich via GitHub Actions
  </footer>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_inhalt)

print("Alle 4 Diagramme und die aktualisierte index.html wurden erfolgreich erstellt!")
