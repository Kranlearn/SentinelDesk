# SentinelDesk

SentinelDesk est un laboratoire local de supervision de securite. Il transforme des evenements techniques en alertes lisibles, les classe avec des regles explicables et les historise dans SQLite.

## MVP actuel

- API HTTP locale en Python standard library
- stockage SQLite normalise
- detection de mots-cles suspects
- niveaux `info`, `warning` et `critical`
- dashboard web responsive
- demonstration reproductible sans connexion externe

## Lancer le projet

```powershell
cd "C:\Users\HP OMEN\Documents\SentinelDesk"
python api.py
```

Puis ouvre http://127.0.0.1:8010/ et clique sur **Generer une demonstration**.

## Envoyer un evenement

```powershell
$body = '{"source":"Windows Lab","event_type":"login","message":"Failed login detected"}'
Invoke-RestMethod -Uri http://127.0.0.1:8010/api/events -Method Post -ContentType 'application/json' -Body $body
```

Le projet est volontairement local et defensif. Les prochaines evolutions pourront ajouter la lecture de journaux Windows, des regles configurables, des rapports et une authentification.



----------------------------------------------------------------------------------------------------

## English version

SentinelDesk is a local security monitoring laboratory. It transforms technical events into readable alerts, classifies them with explainable rules, and stores them in SQLite.

### Current MVP

- Local HTTP API built with Python's standard library
- Normalized SQLite storage
- Suspicious keyword detection
- `info`, `warning`, and `critical` severity levels
- Responsive web dashboard
- Reproducible demonstration with no external connection

### Run the project

```powershell
cd "C:\Users\HP OMEN\Documents\SentinelDesk"
python api.py
```

Then open http://127.0.0.1:8010/ and click **Generate demonstration**.

### Send an event

```powershell
$body = '{"source":"Windows Lab","event_type":"login","message":"Failed login detected"}'
Invoke-RestMethod -Uri http://127.0.0.1:8010/api/events -Method Post -ContentType 'application/json' -Body $body
```

The project is intentionally local and defensive. Future improvements may include Windows event log collection, configurable detection rules, reporting, and authentication.
