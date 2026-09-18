# HIMS

Hospital Information Management System — Django REST API with Keycloak SSO.

**Install and run:**

- [Ubuntu](INSTALL_UBUNTU.md)
- [Windows](INSTALL_WINDOWS.md)
- [Index](INSTALL.md)

Identity only in this phase: Keycloak authenticates; Django verifies the JWT and maps roles to permissions.

## Layout

```
hims/                 # this repository
  manage.py
  hims/               # Django project (settings, urls, wsgi)
  identity/           # identity app (tables, JWT, /me)
  keycloak/import/    # realm, clients, demo users
  docker-compose.yml
  INSTALL.md
  INSTALL_UBUNTU.md
  INSTALL_WINDOWS.md
  docs/
```

Quick start (Docker running):

```bash
cp .env.example .env
docker compose up -d --build
```
