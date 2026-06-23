---
name: sonarqube
description: Set up, run, and manage the local SonarQube instance via Docker Compose. Use when asked to start SonarQube, analyze code quality, configure a project, or troubleshoot the local SonarQube setup.
---

Help the user set up and use their local SonarQube instance. Follow the steps relevant to the user's request.

## Stack

- **SonarQube**: `sonarqube:10.6-community` on port `9000`
- **Database**: PostgreSQL 15 (`sonarqube_db`)
- **Compose file**: `/home/larslenon/dev/sonarqube/docker-compose.yml`

---

## Starting SonarQube

```bash
cd /home/larslenon/dev/sonarqube
docker compose up -d
```

- UI available at: http://localhost:9000
- Default credentials: `admin` / `admin` (you will be prompted to change on first login)
- First startup takes ~1–2 minutes for Elasticsearch to initialize

**Check logs if it's slow:**
```bash
docker compose logs -f sonarqube
```

**Verify it's up:**
```bash
curl -s http://localhost:9000/api/system/status | jq .
# Expected: {"status":"UP",...}
```

---

## Stopping SonarQube

```bash
cd /home/larslenon/dev/sonarqube
docker compose down
```

To also remove volumes (full reset):
```bash
docker compose down -v
```

---

## Analyzing a Project

### 1. Generate a token
1. Log in at http://localhost:9000
2. Go to **My Account → Security → Generate Token**
3. Copy the token (shown only once)

### 2. Run analysis with sonar-scanner

Install if needed:
```bash
# macOS/Linux via npm
npm install -g sonar-scanner

# Or download: https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/
```

Run from project root:
```bash
sonar-scanner \
  -Dsonar.projectKey=<project-key> \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=<your-token>
```

### 3. sonar-project.properties (recommended)

Create `sonar-project.properties` in the project root:
```properties
sonar.projectKey=my-project
sonar.projectName=My Project
sonar.sources=src
sonar.exclusions=**/__pycache__/**,**/node_modules/**,**/*.test.*
sonar.host.url=http://localhost:9000
# sonar.token is passed via env or CLI flag — do not commit it
```

Then run simply:
```bash
sonar-scanner -Dsonar.token=$SONAR_TOKEN
```

---

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| Container exits immediately | `vm.max_map_count` too low | `sudo sysctl -w vm.max_map_count=262144` |
| Elasticsearch bootstrap checks | ES checks not disabled | Ensure `SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true` in compose env |
| DB connection refused | Postgres not ready yet | Wait and retry; check `docker compose logs db` |
| 9000 already in use | Port conflict | `lsof -i :9000` and stop the conflicting process |
| Analysis fails: "project not found" | Project key mismatch | Create the project in SonarQube UI first, or use auto-provisioning |

### WSL2-specific: fix vm.max_map_count persistently

Add to `/etc/sysctl.conf` inside WSL:
```
vm.max_map_count=262144
```
Then run `sudo sysctl -p`.

---

## Volumes & Data

| Volume | Purpose |
|---|---|
| `sonarqube_data` | SonarQube app data (projects, rules) |
| `sonarqube_logs` | Log files |
| `sonarqube_extensions` | Plugins |
| `postgresql` | PostgreSQL database files |

Data persists across `docker compose down` (without `-v`).

---

## Useful API Calls

```bash
# System status
curl -u admin:admin http://localhost:9000/api/system/status

# List projects
curl -u admin:admin "http://localhost:9000/api/projects/search"

# Latest analysis for a project
curl -u admin:admin "http://localhost:9000/api/measures/component?component=<project-key>&metricKeys=bugs,vulnerabilities,code_smells,coverage"
```
