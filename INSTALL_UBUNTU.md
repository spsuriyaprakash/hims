# HIMS installation — Ubuntu

Local development only. Keycloak `start-dev`, Django `runserver`, and default passwords. Do not use these in UAT or production.

Tested pattern: Ubuntu 22.04 / 24.04 with Docker Compose v2.

## What you get

| Service | URL | Database |
|---|---|---|
| Postgres | `localhost:5432` | `hims` (Django) and `keycloak` (Keycloak) |
| Redis | `localhost:6379` | cache |
| Keycloak | http://localhost:8080 | `keycloak` |
| Django API | http://127.0.0.1:8000 | `hims` |

- Keycloak admin: http://localhost:8080 — `admin` / `admin` — realm **hims**
- Demo users (password `Passw0rd!`): `anita.rao` (doctor), `priya.nair` (receptionist)

## 1. Install Docker Engine and Compose

Do **not** use the `docker.io` package from Ubuntu’s default repo if you can avoid it. Use Docker’s official packages.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Allow your user to run Docker without `sudo` (then **log out and back in**):

```bash
sudo usermod -aG docker "$USER"
```

Check:

```bash
docker version
docker compose version
```

You need `docker compose` (plugin), not the old `docker-compose` hyphen binary.

## 2. Free ports

```bash
ss -lptn | grep -E ':5432|:6379|:8080|:8000' || true
```

If something else owns those ports, stop it or change the left-hand ports in `docker-compose.yml`.

## 3. Get the code and `.env`

```bash
git clone <repository-url>
cd hims
cp .env.example .env
```

`.env` is not in git. Compose **requires** this file.

## 4. Recommended: run everything in Docker

```bash
docker compose up -d --build
```

Wait for Keycloak (30–90 seconds on first start):

```bash
docker compose logs -f keycloak
```

When Keycloak is listening on 8080:

```bash
docker compose ps
curl -s http://127.0.0.1:8000/api/v1/healthz
```

Expect `{"database": true, "redis": true}`.

Stop:

```bash
docker compose down
```

Wipe Postgres data (init scripts run again):

```bash
docker compose down -v
```

## 5. Optional: Django on the host

Infra still runs in Docker. Django runs on Ubuntu Python.

```bash
sudo apt-get install -y python3 python3-venv python3-pip
# Ubuntu 24.04 often has 3.12. On 22.04, 3.10 is enough (Django 5.1 needs 3.10+).

docker compose up -d postgres redis keycloak

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_identity --demo-user
python manage.py runserver
```

Do not start the compose `django` service at the same time (port 8000).

Host `.env` already uses `127.0.0.1` for Postgres and Redis. That is correct on the host.

## 6. Verify Keycloak + API

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/realms/hims/protocol/openid-connect/token \
  -d grant_type=password \
  -d client_id=hims-web \
  -d username=anita.rao \
  -d password='Passw0rd!' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s http://127.0.0.1:8000/api/v1/me -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8000/api/v1/probe/encounter-create -H "Authorization: Bearer $TOKEN"
```

- Doctor `anita.rao`: probe **200**
- Receptionist `priya.nair`: probe **403**

Password grant is for local tests only.

## 7. Ubuntu-specific problems

**`permission denied` talking to Docker**  
You are not in the `docker` group, or you did not re-login after `usermod`.

**`Cannot connect to the Docker daemon`**  
`sudo systemctl start docker` and `sudo systemctl enable docker`.

**`env_file: .env` not found**  
You are not in the repo root, or you skipped `cp .env.example .env`.

**`ss` / `curl` missing**  
`sudo apt-get install -y iproute2 curl`

**Firewall**  
Local `localhost` traffic is fine. You do not need to open 8080/8000 on `ufw` unless you access the VM from another machine.

**Realm missing / Keycloak 404**  
Wait for first boot. Then `docker compose down -v && docker compose up -d --build`.

## 8. Layout and settings

```
hims/                 # clone root
  manage.py
  hims/settings/      # base.py, local.py, uat.py, production.py
  identity/
  docker-compose.yml
  .env.example
```

`manage.py` uses `hims.settings.local`.
