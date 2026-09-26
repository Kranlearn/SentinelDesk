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

## Reliability and observability

SentinelDesk now includes a small SRE-oriented reliability layer:

- `/api/health` confirms that the process is responding;
- `/api/ready` verifies that SQLite is reachable and reports its size;
- `/api/version` exposes the running application version;
- `/api/metrics` reports event totals, request count, error rate, and average latency;
- requests are emitted as structured JSON logs;
- request bodies are size-limited and invalid payloads receive explicit errors;
- `/api/backup` creates a timestamped SQLite backup in `backups/`;
- automated tests cover validation, persistence, runtime metrics, and backups.

### Configuration

The service can be configured without editing source code:

```powershell
$env:SENTINEL_HOST = "127.0.0.1"
$env:SENTINEL_PORT = "8010"
$env:SENTINEL_DATABASE = ".\sentineldesk.db"
python api.py
```

The request body limit can be adjusted with `SENTINEL_MAX_REQUEST_BYTES`. The default is 16 KB.

## Alert aggregation and deduplication

SentinelDesk groups identical events during a configurable time window instead of creating one alert for every repetition. Event identity is based on the source, event type, severity, and message.

For example, 100 identical failed-login events received within 60 seconds are stored as one alert with `occurrences: 100` and an updated `last_seen` timestamp. Events received after the window create a new alert group.

The default aggregation window is 60 seconds and can be changed with:

```powershell
$env:SENTINEL_AGGREGATION_WINDOW_SECONDS = "120"
python api.py
```

The dashboard distinguishes unique alerts from total occurrences, so the operator can see both the noise reduction and the real event volume.

## Agrégation et déduplication

SentinelDesk regroupe les événements identiques pendant une fenêtre configurable au lieu de créer une alerte pour chaque répétition. L’identité d’un événement repose sur sa source, son type, sa sévérité et son message.

Ainsi, 100 événements identiques de tentative de connexion échouée reçus en moins de 60 secondes sont conservés comme une seule alerte avec `occurrences: 100` et une date `last_seen` actualisée. Au-delà de la fenêtre, un nouveau groupe d’alerte est créé.

La fenêtre par défaut est de 60 secondes et se configure avec `SENTINEL_AGGREGATION_WINDOW_SECONDS`. Le dashboard sépare les alertes uniques du nombre total d’occurrences.

### Reliability endpoints

```powershell
Invoke-RestMethod http://127.0.0.1:8010/api/health
Invoke-RestMethod http://127.0.0.1:8010/api/ready
Invoke-RestMethod http://127.0.0.1:8010/api/metrics
Invoke-RestMethod http://127.0.0.1:8010/api/backup -Method Post
```
