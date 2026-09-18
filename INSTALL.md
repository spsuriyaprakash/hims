# HIMS installation

Pick the guide for your OS:

| OS | Guide |
|---|---|
| Ubuntu 22.04 / 24.04 | [INSTALL_UBUNTU.md](INSTALL_UBUNTU.md) |
| Windows 10 / 11 | [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md) |

This stack is **local development only** (Keycloak `start-dev`, Django `runserver`, default passwords).

## Shared facts

| Service | URL |
|---|---|
| Keycloak | http://localhost:8080 (`admin` / `admin`), realm `hims` |
| Django API | http://127.0.0.1:8000 |
| Health | http://127.0.0.1:8000/api/v1/healthz |

Demo users, password `Passw0rd!`: `anita.rao` (doctor), `priya.nair` (receptionist).

Every machine: copy `.env.example` to `.env`, then `docker compose up -d --build`. Docker must be running. Ports **5432**, **6379**, **8080**, **8000** must be free.

macOS: use the Ubuntu guide for commands (`cp`, `curl`, `docker compose`). Install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/) instead of apt.
