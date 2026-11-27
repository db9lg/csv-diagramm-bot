import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Datei zeilenweise einlesen (ignoriert Kommentare '#' und Leerzeilen)
zeilen = []
with open("clt_f107_nf_final.txt", "r", encoding="latin1") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        teile = line.split(":")
        if len(teile) >= 4:
            zeilen.append({
                "date": teile[0].strip(),
                "hour": teile[1].strip(),
                "sfu": teile[3].strip()
            })

df = pd.DataFrame(zeilen)

# 2. Datum und Zahlenwerte sicher umwandeln
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
df["sfu"] = pd.to_numeric(df["sfu"], errors="coerce")
df = df.dropna(subset=["date", "sfu"])

if df.empty:
    raise ValueError("Keine gültigen Datenzeilen in der Datei gefunden!")

# 3. Pro Tag einen Wert wählen (bevorzugt 12 Uhr UTC Noonflux)
df["is_noon"] = (df["hour"] == 12).astype(int)
df_daily = (
    df.sort_values(["date", "is_noon"], ascending=[True, False])
    .groupby("date", as_index=False)
    .agg({"sfu": "first"})
)

# 4. Auf die letzten 30 Tage eingrenzen
letztes_datum = df_daily["date"].max()
start_datum = letztes_datum - pd.Timedelta(days=29)
df_30 = df_daily[df_daily["date"] >= start_datum].sort_values("date")

# 5. Liniendiagramm erstellen
fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

ax.plot(
    df_30["date"],
    df_30["sfu"],
    marker="o",
    linestyle="-",
    linewidth=2,
    markersize=5,
    color="#1f77b4"
)

ax.set_title(
    f"Solar Flux Index (F10.7) – Letzte 30 Tage (Stand: {letztes_datum.strftime('%d.%m.%Y')})",
    fontsize=13,
    fontweight="bold",
    pad=12
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
print(f"Erfolgreich erstellt: {len(df_30)} Tage bis {letztes_datum.strftime('%Y-%m-%d')}.")
