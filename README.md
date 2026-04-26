# Rollladensteuerung

[![HACS Custom][hacs-badge]][hacs-url]
[![Validate][validate-badge]][validate-url]

Eine Home Assistant Custom Integration, die die Logik des `Rollladensteuerung 2`-Blueprints als eigenständige Integration abbildet – konfigurierbar über die UI, keine YAML-Automationen nötig.

## Features

- Pro Cover eine eigene Config-Entry-Instanz
- Vollständige Blueprint-Logik in Python:
  - Nacht-/Tag-Beschattung mit konfigurierbaren Höhen
  - Fenster-/Türkontakt-Erkennung (mehrere Sensoren pro Cover)
  - Richtungsbasierte Beschattung (`binary_sensor.richtung<suffix>`)
  - PC-Beschattung (separate Richtungslogik)
  - Kino-/Filmeabend-Modus
  - Morgens-Öffnen-Funktion
  - Schlafen- und Zu-Modus
  - Beschattungs-Hysterese mit 4-Minuten-Verzögerung beim Abschalten
- Diagnostik-Sensor je Cover mit letztem Entscheidungsgrund

## Installation via HACS

1. HACS → Integrationen → ⋮ → Custom Repositories
2. URL: `https://github.com/revilo91/rollladensteuerung`
3. Kategorie: `Integration`
4. Repository hinzufügen, dann installieren

## Manuelle Installation

```bash
cp -r custom_components/rollladensteuerung \
      /config/custom_components/rollladensteuerung
```

HA neu starten.

## Konfiguration

**Einstellungen → Integrationen → + Hinzufügen → Rollladensteuerung**

| Feld | Pflicht | Beschreibung |
|---|---|---|
| Cover-Entität | ✅ | Die zu steuernde `cover.*`-Entität |
| Fenster-/Türkontakte | – | Mehrere `binary_sensor.*` möglich |
| Richtungs-Suffix | – | z. B. `suden` → `binary_sensor.richtungsuden` |
| Raum-Automatik | ✅ | `input_select.*` mit Werten wie `Automatik`, `Erzwungen`, `Inaktiv`, `Manuell`, `PC Automatik`, `PC Erzwungen`, `Schlafen`, `Zu` |
| Beschattungs-Hysterese | ✅ | `binary_sensor.beschattung_hysterese` |
| Tag/Nacht-Modus | ✅ | `input_boolean.tag_nacht_modus` |
| Höhe Nacht | ✅ | `input_number.beschattungshohe_nacht` |
| Höhe Tag | ✅ | `input_number.beschattungshohe_tag` |
| Höhe Schlafen | – | `input_number.beschattungshohe_schlafen` |
| PC-Schalter | – | `switch.buro_steckdose_*` o. ä. |
| Kino-Schalter | – | `switch.kino` |
| Morgens-Auf Schalter | – | `switch.rolllade_ankleide_morgens_auf` |
| Morgens-Funktion aktiv | – | Boolean – ersetzt das Blueprint-Label |
| Filmeabend-Funktion aktiv | – | Boolean – ersetzt das Blueprint-Label |

## Entscheidungslogik (Priorität)

```
1. Nacht + Fenster offen           → Nacht-Höhe
2. Tür offen (kein Fenster)        → Öffnen
3. Nacht + Morgens-Modus aktiv     → Nacht-Höhe
4. Nacht + geschlossen             → Schließen
5. Filmeabend-Label + Kino aktiv   → Schließen
6. Tag + Schlafen                  → Schlafen-Höhe
7. Raum = Zu                       → Schließen
8. Tag + Beschattung + Richtung    → Tag-Höhe
9. Standard                        → Tag: Öffnen / Nacht: Schließen
```

## Diagnostik-Sensor

Jede Instanz erzeugt einen Sensor `sensor.rollladensteuerung_<cover>` mit dem letzten Entscheidungsgrund als `state`.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz
[validate-badge]: https://github.com/revilo91/rollladensteuerung/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/revilo91/rollladensteuerung/actions/workflows/validate.yml
