# Projekt-Richtlinien

## Geltungsbereich

- Dieses Repository enthält eine Home-Assistant-Custom-Integration mit UI-basierter Einrichtung über Config Entries. Führe keine YAML-only-Konfiguration ein, außer wenn die Aufgabe das ausdrücklich verlangt.
- Änderungen sollen sich auf die Integration unter `custom_components/covercontroladvanced` konzentrieren und die üblichen Home-Assistant-Muster für Config Flow, Entity-Setup und asynchronen Lebenszyklus beibehalten.

## Python- und Home-Assistant-Konventionen

- Bevorzuge vollständig typisiertes Python und halte die vorhandene, bewusst einfache Modulstruktur bei. Füge keine zusätzlichen Abstraktionsschichten ohne klaren Nutzen ein.
- Nutze Home-Assistant-Async-APIs konsequent von Ende zu Ende. Kein blockierendes I/O, keine synchronen Sleeps und keine lang laufende Arbeit in Controller- oder Entity-Code.
- Behalte das bestehende Setup-Muster bei: Der Controller wird in `__init__.py` erzeugt, unter `hass.data[DOMAIN][entry.entry_id]` gespeichert und in der Sensor-Plattform wiederverwendet.
- Service-Aufrufe und Zustandsbeobachtung sollen sich an Home-Assistant-Helpern wie `async_track_state_change_event`, `async_call_later` und `hass.services.async_call` orientieren.

## Integrationsspezifische Regeln

- Betrachte `config_flow.py`, `const.py`, `controller.py` und `sensor.py` als Kernvertrag der Integration. Änderungen an Konfigurationsschlüsseln in `const.py` müssen immer in Config Flow, Laufzeitlogik und Übersetzungen nachgezogen werden.
- Der Diagnose-Sensor zeigt den Entscheidungsgrund des Controllers an. Wenn du die Entscheidungslogik änderst, muss `last_reason` weiterhin verständlich, kurz und für Nutzer lesbar bleiben.
- Die Integration arbeitet mit in Config Entries gespeicherten Home-Assistant-Entity-IDs. Ersetze diese nicht durch harte Annahmen oder abgeleitete Werte, außer wenn die Aufgabe ausdrücklich eine Migration verlangt.
- Die bestehende Logik unterscheidet Tag/Nacht, Beschattungshysterese, Raummodi, Richtungssensoren, optionale Schlafposition und optionalen Event-Schalter. Dieses Verhalten bleibt erhalten, solange die Aufgabe keine geänderten Fachregeln verlangt.

## Kanonische Benennung

- Die technische Kennung der Integration ist `covercontroladvanced`. Dieser Wert muss für den Komponentenordner, den Manifest-Domain-Wert und die `DOMAIN`-Konstante konsistent bleiben.
- Der sichtbare Produktname ist `Cover Control Advanced`. Verwende diesen Namen in README, HACS-Metadaten, Config-Flow-Texten und Entity-Namen.
- Repository- und URL-Namen dürfen weiterhin `CoverControlAdvanced` verwenden. Vermische diese GitHub-Schreibweise aber nicht mit der technischen Integration-Domain.

## Übersetzungen und Dokumentation

- Jede nutzerseitige Änderung an Config-Flow-Feldern, Titeln oder Abort-Meldungen muss in beiden Übersetzungsdateien unter `custom_components/covercontroladvanced/translations/` gespiegelt werden.
- README-Beispiele, Installationspfade und Begriffe müssen zum tatsächlichen Integrationsordner und zur aktuellen Laufzeitlogik passen.

## Validierung

- Führe nach substanziellen Python-Änderungen `ruff check custom_components/` aus.
- Wenn Änderungen Manifest, Struktur, Übersetzungen oder Home-Assistant-Metadaten betreffen, berücksichtige zusätzlich die CI-Erwartungen aus `.github/workflows/validate.yml`, insbesondere HACS-Validation und Hassfest.


## Visual Architecture
```mermaid
flowchart TD
    %% Room Level
    Room["🏠 Room"]
    
    subgraph RoomParams [Room Configuration]
        State["Status Dropdown<br/>(Shading / Forced / Inactive / Closed)"]
        BaseHeight["Global Shading Height"]
        Hysteresis["Binary Sensor (Hysteresis)"]
    end

    subgraph EventSwitch [Event Control]
        Toggle["Event Switch (ON/OFF)"]
        EvHeight{{"Event-specific Height"}}
    end

    %% Links to Room
    Room --- State
    Room --- BaseHeight
    Room --- Hysteresis
    Room --- Toggle
    Toggle ---> EvHeight

    %% Stacked Covers using 'docs' shape
    CoverStack@{ shape: docs, label: "Covers 1..N" }
    
    Room ==> CoverStack

    subgraph CoverDetails [Cover Instance Specification]
        direction TB
        
        %% Separate Azimuth Nodes
        StartAz["Start Azimuth"]
        EndAz["End Azimuth"]
        
        %% Stacked Contacts with Device Class
        ContactStack@{ shape: docs, label: "Contacts 1..N" }
        DClass{{"device_class:<br/>door / window"}}
        
        ContactStack --- DClass
    end

    %% Connect the stack to its shared definition
    CoverStack --- StartAz
    CoverStack --- EndAz
    CoverStack --- ContactStack    
 ```  
## Technical Specification (Copilot Context)
- **Entity: Room**
    - **State (Dropdown Helper):** Defines the global operating mode. Valid values: `Shading`, `Forced Shading`, `Inactive`, `Closed`.
    - **Hysteresis (Binary Sensor):** Acts as a buffer to prevent rapid movement due to fluctuating sensor values.
    - **Shading Height (Value):** The default target position for all covers in the room.
    - **Event Switch:** A specialized toggle that activates a secondary set of height settings, overriding the default room height.
    - **1:N Relationship:** A single Room manages a collection of $N$ associated Covers.
- **Entity: Cover**
    - **Start Azimuth:** The sun's angle at which shading for this specific cover begins.
    - **End Azimuth:** The sun's angle at which shading for this specific cover ends.
    - **1:N Relationship (Contacts):** Every cover is linked to $N$ binary sensors.
    - **Contact Attribution** (`device_class`):
        - *Logic Rule:* Contacts primarily serve as safety or lockout conditions (e.g., "lock-out protection") specific to that individual cover.
        - `window`: Triggers ventilation or prevents closing if open.
        - `door`: Provides lock-out protection to prevent accidental closure while people are outside.

        
