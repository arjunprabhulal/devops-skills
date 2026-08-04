# Dockerfile patterns

Concrete templates for the patterns `SKILL.md` argues for. Copy the stage that matches your
runtime, then trim what you don't need — every extra `RUN` is a layer someone has to explain later.

## Contents

- Go: multi-stage into `scratch`
- Node: multi-stage into distroless
- Python: multi-stage with a venv handoff
- Build secrets: `--mount=type=secret`
- `.dockerignore`
- `HEALTHCHECK`
- PID 1 and signal handling

## Go: multi-stage into `scratch`

A compiled, statically-linked binary needs nothing at runtime, not even a libc, so `scratch` — zero
bytes before your binary lands — is the right base.

```dockerfile
FROM golang:1.22 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -o /app ./cmd/server

FROM scratch AS runtime
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build /app /app
USER 65532:65532
ENTRYPOINT ["/app"]
```

The cache mounts persist `go mod download` and the build cache across builds without baking either
into a layer — cold builds hit the network once, warm builds hit neither. `scratch` has no shell or
`/etc/passwd`, so copy CA certs explicitly (needed for outbound TLS) and set `USER` numerically.

## Node: multi-stage into distroless

Node needs its runtime, so `scratch` is out, but production `node_modules` should never include
`devDependencies` or build tools.

```dockerfile
FROM node:20 AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --omit=dev

FROM node:20 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm run build

FROM gcr.io/distroless/nodejs20-debian12 AS runtime
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER 1000:1000
EXPOSE 3000
ENTRYPOINT ["dist/server.js"]
```

Splitting `deps` from `build` means production `node_modules` never touches devDependencies, even
transiently. Distroless ships a Node runtime and nothing else — no shell, no package manager, no
coreutils — most of what makes `scratch` attractive, minus managing a static binary yourself.

## Python: multi-stage with a venv handoff

Python can't produce a static binary, but you can still keep the compiler and wheel cache out of
the runtime stage by building into a venv and copying the venv, not the site-packages directly.

```dockerfile
FROM python:3.12-slim AS build
WORKDIR /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

FROM python:3.12-slim AS runtime
RUN groupadd -g 10001 app && useradd -u 10001 -g app -M app
COPY --from=build /venv /venv
COPY --chown=app:app . /app
WORKDIR /app
ENV PATH="/venv/bin:$PATH"
USER 10001:10001
CMD ["python", "-m", "app"]
```

`-slim` keeps `apt` and a shell for debugging without the full image's build toolchain; move to
distroless's Python variant once you're confident you'll never need to `exec` into the container.

## Build secrets: `--mount=type=secret`

Never `ARG`/`ENV` a credential — both persist in `docker history` even after a later `RUN` removes
the file. Mount it instead; it's available only for that one `RUN` and never touches a layer.

```dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci --omit=dev
```

```bash
docker build --secret id=npmrc,src="$HOME/.npmrc" -t app .
```

## `.dockerignore`

Everything not excluded is sent to the daemon as build context — one stray `COPY . .` away from
landing in a layer.

```
.git
**/node_modules
**/__pycache__
.env*
*.log
dist
build
coverage
Dockerfile*
.dockerignore
```

## `HEALTHCHECK`

Gives `docker ps` a liveness signal without an external prober. Kubernetes ignores it in favor of
its own probes, but it's cheap insurance for anything run outside an orchestrator.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/healthz || exit 1
```

Keep the probe dependency-free — `wget` or `curl` if the base has it, or a tiny compiled check for
`scratch`/distroless images where neither exists.

## PID 1 and signal handling

A process running as PID 1 gets no default signal handlers from the kernel — if your app doesn't
trap `SIGTERM`, `docker stop` waits out the grace period and sends `SIGKILL`, every deploy.
Shell-form `CMD` makes it worse, wrapping your process in `/bin/sh -c`, which swallows the signal
before your app sees it. Use exec form so your process actually is PID 1:

```dockerfile
CMD ["node", "server.js"]
```

If your app forks children, doesn't handle signals itself, or you'd rather not find out which,
add a minimal init that reaps zombies and forwards signals:

```dockerfile
FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "server.js"]
```

`docker run --init` does the same at the daemon level without touching the Dockerfile; bake in
`tini` when the image also needs to run correctly outside Docker's control (bare `containerd`, some
CI runners).
