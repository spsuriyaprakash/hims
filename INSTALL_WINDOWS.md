# HIMS installation — Windows

Local development only. Keycloak `start-dev`, Django `runserver`, and default passwords. Do not use these in UAT or production.

Use **Windows 10/11** with **WSL2** and **Docker Desktop**. PowerShell is assumed below. Git Bash also works if you prefer Linux-style commands (then see [INSTALL_UBUNTU.md](INSTALL_UBUNTU.md) for command shape).

## What you get

| Service | URL | Database |
|---|---|---|
| Postgres | `localhost:5432` | `hims` (Django) and `keycloak` (Keycloak) |
| Redis | `localhost:6379` | cache |
| Keycloak | http://localhost:8080 | `keycloak` |
| Django API | http://127.0.0.1:8000 | `hims` |

- Keycloak admin: http://localhost:8080 — `admin` / `admin` — realm **hims**
- Demo users (password `Passw0rd!`): `anita.rao` (doctor), `priya.nair` (receptionist)

## 1. Install prerequisites

1. **WSL2** (from an elevated PowerShell):

   ```powershell
   wsl --install
   ```

   Reboot if Windows asks. Ubuntu from the Microsoft Store is fine.

2. **Docker Desktop for Windows**  
   https://docs.docker.com/desktop/setup/install/windows-install/  
   During setup, enable **Use WSL 2 based engine**. Start Docker Desktop and wait until it says running.

3. **Git for Windows**  
   https://git-scm.com/download/win  
   Installer option: **Checkout as-is, commit Unix-style LF** (important for `docker/postgres/init-databases.sh`).

4. Check in PowerShell:

   ```powershell
   docker version
   docker compose version
   git --version
   ```

You need `docker compose` (space), which Docker Desktop includes.

## 2. Free ports

These must be free on Windows: **5432**, **6379**, **8080**, **8000**.

```powershell
netstat -ano | findstr "5432 6379 8080 8000"
```

IIS, another Postgres, or an old Django `runserver` often occupy 8000 or 8080. Stop those processes or change the left-hand ports in `docker-compose.yml`.

## 3. Get the code and `.env`

```powershell
git clone <repository-url>
cd hims
copy .env.example .env
```

`.env` is not in git. Compose **requires** this file in the same folder as `docker-compose.yml`.

If `copy` fails in PowerShell:

```powershell
Copy-Item .env.example .env
```

## 4. Recommended: run everything in Docker

From the repo folder (`hims`), with Docker Desktop running:

```powershell
docker compose up -d --build
```

First start can take several minutes (image pull + Keycloak). Watch Keycloak:

```powershell
docker compose logs -f keycloak
```

Press `Ctrl+C` to stop following logs (containers keep running).

Check:

```powershell
docker compose ps
curl.exe -s http://127.0.0.1:8000/api/v1/healthz
```

Expect `{"database": true, "redis": true}`.

Stop:

```powershell
docker compose down
```

Wipe database volumes (needed if Postgres init did not create `hims` / `keycloak`):

```powershell
docker compose down -v
```

## 5. Optional: Django on Windows (or in WSL)

### Option A — Django inside WSL Ubuntu (preferred if you develop on Windows)

Open Ubuntu (WSL), clone the repo on the **Linux filesystem** (`~/hims`, not `C:\...` — disk performance is much better), then follow [INSTALL_UBUNTU.md](INSTALL_UBUNTU.md) from step 3. Keep Docker Desktop running; it provides the engine to WSL.

### Option B — Django on native Windows Python

1. Install Python 3.12 from https://www.python.org/downloads/windows/  
   Tick **Add python.exe to PATH**.

2. Start infra only:

   ```powershell
   docker compose up -d postgres redis keycloak
   ```

3. Create a venv in the repo:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -U pip
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py seed_identity --demo-user
   python manage.py runserver
   ```

If PowerShell blocks the activate script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Do not run the compose `django` service at the same time as host `runserver`.

## 6. Verify Keycloak + API

Windows includes `curl.exe`. In PowerShell:

```powershell
$body = @{
  grant_type = "password"
  client_id  = "hims-web"
  username   = "anita.rao"
  password   = "Passw0rd!"
}
$resp = Invoke-RestMethod -Method Post -Uri "http://localhost:8080/realms/hims/protocol/openid-connect/token" -Body $body
$token = $resp.access_token

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/me" -Headers @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/probe/encounter-create" -Headers @{ Authorization = "Bearer $token" }
```

Or with `curl.exe`:

```powershell
curl.exe -s -X POST http://localhost:8080/realms/hims/protocol/openid-connect/token -d grant_type=password -d client_id=hims-web -d username=anita.rao -d password=Passw0rd!
```

Copy `access_token` from the JSON, then:

```powershell
curl.exe -s http://127.0.0.1:8000/api/v1/me -H "Authorization: Bearer PASTE_TOKEN_HERE"
```

- Doctor `anita.rao`: probe **200**
- Receptionist `priya.nair`: probe **403**

## 7. Windows-specific problems

**Docker Desktop is not running**  
Start it from the Start menu. Whale icon in the tray should be idle, not “starting”.

**`error during connect: ... dockerDesktopLinuxEngine`**  
WSL2 / Docker Desktop not ready. Restart Docker Desktop. Run `wsl -l -v` and confirm a distro is **Running**.

**`env_file: .env` not found**  
Create `.env` in the folder that contains `docker-compose.yml`. File Explorer: show file extensions so it is not named `.env.txt`.

**Postgres databases missing**  
`init-databases.sh` needs **LF** line endings. If Git converted it to CRLF, the script can fail silently on first volume create:

```powershell
docker compose down -v
```

Then in Git:

```powershell
git config core.autocrlf input
git checkout -- docker/postgres/init-databases.sh
docker compose up -d --build
```

**Port 8080 in use**  
Skype (older), IIS, or another Java app. Change `"8080:8080"` to `"8081:8080"` and use http://localhost:8081 — then also change Keycloak URLs in `.env`.

**Hyper-V / virtualization disabled**  
Enable virtualization in BIOS and “Windows features” → Virtual Machine Platform.

**Cloned under `C:\Users\...\OneDrive\...`**  
Avoid OneDrive for the repo if Docker file watching is flaky. Use `C:\src\hims` or WSL `~/hims`.

## 8. Layout and settings

```
hims\                 # clone root
  manage.py
  hims\settings\      # base.py, local.py, uat.py, production.py
  identity\
  docker-compose.yml
  .env.example
```

`manage.py` uses `hims.settings.local`.
