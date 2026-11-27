import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1. Datei einlesen (Kommentare mit '#' ignorieren, Trennzeichen ':')
spalten = [
    "date", "hour", "frequency", "sfu", "square_distance_sun",
    "central_meridian_sun", "carrington_longitude", "carrington_cycle",
    "sigma", "minute_val_included"
]

df = pd.read_csv(
    "daten.csv",
    sep=":",
    comment="#",
    names=spalten,
    encoding="latin1"
)

# 2. Datum formatieren und Werte bereinigen
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
df["sfu"] = pd.to_numeric(df["sfu"], errors="coerce")
df = df.dropna(subset=["date", "sfu"])

# 3. Pro Tag einen Wert wählen (bevorzugt 12 Uhr UTC Noonflux, sonst Tagesmittel)
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

# Titel und Achsenbeschriftungen
ax.set_title(
    f"Solar Flux Index (F10.7) – Letzte 30 Tage (Stand: {letztes_datum.strftime('%d.%m.%Y')})",
    fontsize=13,
    fontweight="bold",
    pad=12
)
ax.set_xlabel("Datum (UTC)", fontsize=10)
ax.set_ylabel("Solar Flux Density [sfu]", fontsize=10)

# Datumsformat auf der X-Achse schön lesbar machen
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m."))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
plt.xticks(rotation=45)

# Gitterlinien und Rahmen anpassen
ax.grid(True, linestyle="--", alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("sfu_30tage.png")
print(f"Diagramm erstellt mit {len(df_30)} Tagen bis {letztes_datum.strftime('%Y-%m-%d')}.")
