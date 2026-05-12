# Run JuPedSim Web Locally (Docker)

Two ways to run the simulator on your own machine, depending on how much control you want.

## Quick start — one container (self-host)

The fastest path. Bundles the frontend, both backends, and MongoDB into a single image. No clone, no compose file, no `.env`, no OAuth setup.

```bash
docker run -d \
  --name jupedsim \
  -p 8080:8080 \
  -v jupedsim-data:/data \
  --memory 4g \
  jupedsim/jupedsim-web:latest
```

Open: http://localhost:8080

Stop cleanly (mongod needs ~60 s on a busy DB):

```bash
docker stop --time 60 jupedsim
```

The `/data` volume holds MongoDB, scenario uploads, and the backend's SQLite state, so your scenarios survive `docker restart` and `docker rm`. Allow ~60 s on first start.

**Security note**: this image disables OAuth and serves every request as an anonymous "Local User". It's meant for local self-host. Do not expose port 8080 to the public internet.

**Licensing note**: the all-in-one image bundles MongoDB Community, which is distributed under the Server Side Public License (SSPL) v1. See the license text at https://www.mongodb.com/licensing/server-side-public-license and review its requirements for your intended use and deployment model.

## Multi-container — separate frontend, backends, and MongoDB

Use this when you want per-service updates, an external MongoDB, or to front the stack with OAuth.

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Access to image namespace: `jupedsim/*`

### Start

```bash
cd docker
cp .env.example .env
docker compose --env-file .env -f docker-compose.yml pull
docker compose --env-file .env -f docker-compose.yml up -d
```

Open: http://localhost:8080

### Stop

```bash
docker compose --env-file .env -f docker-compose.yml down
```

### Update to a Specific Image Tag

Set `IMAGE_TAG` in `docker/.env`, then pull and restart:

```bash
docker compose --env-file .env -f docker-compose.yml pull
docker compose --env-file .env -f docker-compose.yml up -d
```

## Troubleshooting

- If image pulls fail with `manifest unknown`, verify `IMAGE_TAG` exists.
- If pushes/pulls fail with auth errors, run `docker login`.
- If the frontend container crashes with `host not found in upstream` on a version earlier than v1.6, upgrade to v1.6 or later — the upstream hostnames were aligned with the compose service names.
