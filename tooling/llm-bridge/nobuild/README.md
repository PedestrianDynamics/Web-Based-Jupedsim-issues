# LLM bridge — no-rebuild bring-up (prototype)

One command, three **stock** images, nothing built. This replaces the
"build a custom viewer image with the button baked in" step from
`LLM_BRIDGE_SETUP.md`.

```bash
docker compose -f tooling/llm-bridge/nobuild/docker-compose.yml up
```

Then open <http://localhost:8081/draw>. The **Bridge** button is already there;
it points at the bridge on `127.0.0.1:8090`.

## How it works

| Service | Image (stock) | Role |
|---------|---------------|------|
| `viewer` | `jupedsim/jupedsim-web:latest` | The published app, unmodified. |
| `proxy`  | `nginx:1.27-alpine` | Injects `bridge-button.js` into every HTML page via `sub_filter` and strips CSP. |
| `bridge` | `python:3.12-slim` | Runs `bridge_server.py` (stdlib only) by mounting the parent dir. |

No `Dockerfile`, no custom tag, no rebuild when the app updates — bump
`VIEWER_IMAGE` and restart.

## Why a proxy instead of a custom image

The button only needs two things the stock image doesn't give it:

1. a `<script>` tag on the page — added by nginx `sub_filter`;
2. permission to load that script and `fetch()` the bridge — the proxy drops
   `Content-Security-Policy` so both are allowed.

The bridge already sends `Access-Control-Allow-Origin: *`, so the cross-origin
call from `:8081` to `:8090` works without further changes.

## Verify before relying on it (prototype caveats)

- Confirm the button actually appears — if the app serves gzipped HTML from an
  inner layer, `sub_filter` won't fire. Fix: the proxy already sends
  `Accept-Encoding ""` upstream; verify with `curl -s localhost:8081/draw | grep __bridge`.
- Confirm the stock image serves the SPA on `:8080` (the all-in-one image does;
  the compose `frontend` service listens on `:80` — adjust `proxy_pass` if you
  target that stack instead).
- `docker compose down -v` to reset volumes.
