---
applyTo: "custom_components/covercontroladvanced/**/*.py"
description: "Verwenden, wenn Python-Dateien der Home-Assistant-Integration angepasst werden, insbesondere Setup-, Config-Flow-, Controller- oder Sensorlogik."
---

# Python-Dateien der Integration

- Halte Änderungen klein und lokal. Bevorzuge Anpassungen in den bestehenden Dateien statt neue Hilfsmodule oder zusätzliche Schichten einzuführen.
- Bleibe vollständig asynchron. Nutze Home-Assistant-Helper und Services statt blockierender Logik.
- Wenn du Konfigurationsschlüssel, Entity-Attribute oder Entscheidungslogik änderst, prüfe immer die Folgewirkung auf Config Flow, Controller, Sensor und Übersetzungen.
- `last_reason` ist Teil der Diagnoseoberfläche. Formuliere neue Gründe kurz, stabil und für Endnutzer verständlich.
- Nutze die technische Kennung `covercontroladvanced` konsistent für `DOMAIN`, Manifest-Domain und abgeleitete Unique IDs.
