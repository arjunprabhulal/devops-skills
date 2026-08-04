---
name: containerization
description: Packages an application into a container image that is small, reproducible, and safe to run — Dockerfiles, layer caching, multi-stage builds, non-root users, and runtime configuration. Use this whenever the user is writing a Dockerfile, mentions Docker or OCI images, image size or build times, or is preparing an application to run on Kubernetes. For orchestrating those images use `kubernetes-operations`; for scanning them use `image-scanning`.
license: MIT
---

# Containerization

A container image is a build artifact meant to be byte-identical everywhere it runs. Most
Dockerfile trouble comes from treating it like a virtual machine — installing a shell's worth of
tools, running as root, and rebuilding the world on every code change.

Aim for three properties: **small**, **reproducible**, and **least-privileged**. A change that
does not move one of those is not worth making.

For language-specific multi-stage templates, distroless runtimes, and BuildKit cache and secret
mounts, read `references/dockerfile-patterns.md`.

## 1. Order layers by how often they change

Docker caches per layer and invalidates every layer after the first change. Put the stable things
first so a one-line edit does not re-download the internet:

```dockerfile
COPY package.json package-lock.json ./
RUN npm ci                      # cached until dependencies change
COPY . .                        # invalidated on every source change
```

Copying source before installing dependencies means every code change reinstalls everything. This
single reordering is usually the largest build-time win available.

**Done when:** a code-only change does not reinstall dependencies.

## 2. Separate build tooling from the runtime image

A multi-stage build compiles or installs in one stage and copies only the resulting artifact into
a clean final stage. Compilers, headers, and package caches have no business shipping to
production — they add size and give an attacker a toolbox if they land a shell. Name your stages
(`AS build`, `AS runtime`) so the final `COPY --from=build` is unambiguous. Sizing the runtime
image itself — which base to start the final stage from — is `image-optimization`'s job; this
step is about the boundary between building and running.

**Done when:** the runtime image contains no compiler, package manager cache, or source outside
what running requires.

## 3. Pin the base image and run as a non-root user

`FROM node:latest` is not a build input, it is a random number generator — the tag moves under
you and today's build is not tomorrow's. Pin to a digest or an explicit version tag so a rebuild
six months from now produces the same bytes. Then drop privilege: create or reuse a non-root user
and switch to it before the final `CMD`, so a container escape does not hand over root on the
host. Combine this with a read-only root filesystem and a dropped `CAP_*` set where the runtime
supports it.

- **Pin bases** by digest for anything that ships to production, not just a major-version tag.
- **Create the user explicitly** (`RUN adduser -D app`) rather than trusting the base image has one.
- **Set `USER app`** before `CMD`/`ENTRYPOINT`, not after.

**Done when:** the image runs `whoami` as a non-root UID and rebuilding from the same tag does
not silently change the base layer.

## 4. Never bake secrets into a layer

A secret written into any layer — even one later deleted in a subsequent `RUN` — is still
recoverable from the image history. Use build secrets (`RUN --mount=type=secret`) or inject
credentials at runtime via the orchestrator's secret store, never `ARG`/`ENV` for anything
sensitive, since both are visible in `docker history` and image inspection. Managing where those
secrets live long-term is `secrets-management`'s job; this step is only about keeping them out of
the artifact you push.

**Done when:** `docker history` and `docker inspect` on the built image show no credentials, keys,
or tokens.

## 5. Design for the orchestrator, not just `docker run`

A container that starts fast and exits cleanly is easy to run by hand but painful to operate at
scale unless it also exposes the signals an orchestrator needs. Handle `SIGTERM` for graceful
shutdown instead of relying on `SIGKILL` after a timeout. Expose a liveness and readiness
distinction — a process that is running but not yet able to serve traffic should fail readiness,
not liveness. Set resource requests informed by real usage, not guesses, so the scheduler can
place the container sensibly; the scheduling and autoscaling behavior itself belongs to
`kubernetes-operations` and `autoscaling`.

- **Trap `SIGTERM`** and finish in-flight work within the orchestrator's grace period.
- **Expose separate health endpoints** for startup, liveness, and readiness where the runtime
  distinguishes them.
- **Log to stdout/stderr**, not to a file inside the container, so the platform can collect it.

**Done when:** the process shuts down cleanly on `SIGTERM` and reports readiness independently of
liveness.

## 6. Keep the build context minimal

Everything not excluded by `.dockerignore` is sent to the build daemon and is a candidate for
accidental inclusion via a stray `COPY . .`. A bloated context slows every build and risks
shipping `.git`, local `.env` files, or test fixtures into a layer. Treat `.dockerignore` as part
of the Dockerfile, reviewed whenever `COPY` targets change.

**Done when:** `docker build` context transfer size reflects only files the image actually needs.

## Report

State the final image size, the base image and how it is pinned, the user the process runs as,
and what the build stages separate. Name anything you could not strip from the runtime image and
why — that leftover is the remaining attack surface, and naming it is more useful than claiming
the image is minimal.
