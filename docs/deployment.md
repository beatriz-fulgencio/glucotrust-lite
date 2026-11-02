# Deploy GlucoTrust Lite

This setup runs the existing Streamlit app and Qwen model on one Linux server.
Ollama is private to the Docker network. Streamlit is available on the server's
loopback interface; the optional Caddy service exposes it over HTTPS.

## Verification status

On 2026-11-02, both Compose configurations validated, the local Python suite
passed all 46 tests, and the Linux ARM64 image built successfully in Docker
Desktop. A container smoke check confirmed real MiniLM retrieval over 199
passages, Streamlit page rendering and the dosing guard, a non-root app user,
and writable cache/feedback volumes. Server-specific inference latency, the
Ollama container with Qwen, public HTTPS, and the complete hosted assessment
flow still need verification on the chosen server. No cloud server has been
created or app published by this setup work.

An Oracle deployment was attempted on 2026-11-02 in `sa-saopaulo-1`. The API
listed the A1 shape and Ubuntu 24.04 ARM64 image, but launching the 2-OCPU / 12-GB
instance failed with `Out of host capacity`. Oracle's capacity report also
returned `OUT_OF_HOST_CAPACITY` for 1-OCPU / 12-GB and 1-OCPU / 8-GB configurations.
A dedicated virtual network, internet gateway and public subnet were created;
no compute instance or boot disk was created, and there is no live app link.
The local, gitignored `runtime/deployment/oci-state.json` and
`oci-capacity.json` preserve the resource identifiers and capacity report for
resuming without duplicating the network. A dedicated SSH key was created at
`~/.ssh/glucotrust_oracle_ed25519`; it has not been installed on a VM.

## Server requirements

- A Linux server with Docker Engine and Docker Compose v2 installed. Follow the
  [official Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/).
- Start with 4 CPU cores, 16 GB RAM, and 40 GB free disk for a small demo. This is
  an initial estimate, not a measured capacity guarantee. Benchmark your server
  before inviting multiple users. This configuration uses CPU inference.
- Outbound access to Docker registries, PyPI, Hugging Face, and Ollama's model
  registry during setup. Literature fallback also needs outbound Europe PMC access.
- For public HTTPS: a domain pointing to the server and inbound TCP ports 80/443.
  Leave ports 8501 and 11434 closed to public traffic.

### Free Oracle Cloud target

For a zero-cost demo, the current
[Oracle Always Free allowance](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
provides a total of 2 Ampere A1 OCPUs and 12 GB RAM in the account's home region.
Use one `VM.Standard.A1.Flex` instance, an Always Free-eligible Ubuntu ARM64
image, and a 50 GB boot volume within the free storage allocation. The image
has been smoke-tested on Linux ARM64; Qwen response times on the free server
remain unmeasured. This is a smaller demo target than the general starting
estimate above. Keep inference concurrency at one, as configured in Compose.

Oracle may show “Your account is being set up and some features are not
available” immediately after signup. Wait for account activation before treating
missing Compute features as a deployment failure. The console must confirm the
selected resources are within the account's Always Free allocation; promotional
trial credits alone do not establish ongoing free eligibility. Free shape
capacity can be unavailable, and idle instances may be reclaimed.

Host Streamlit and Ollama together on this VM. Visitors access Streamlit over
HTTPS; the app reaches `http://ollama:11434` on Docker's internal network. This
keeps assessment independent of the developer's computer without publishing the
Ollama API. Public application access needs only ports 80/443. Configure SSH
access separately for administration.

Copy the repository to the server and run the commands below from its root. The
image uses an allowlist in `.dockerignore`: local `.env` files, feedback, caches,
and Git history are excluded. Linux dependencies resolve from `pyproject.toml`,
not the macOS-specific lock file. Initial builds require network access and can
take several minutes. No local Python or Ollama installation is needed on the server.

## Start and verify privately

```sh
docker compose config --quiet
docker compose up -d --wait ollama
docker compose exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M
docker compose up -d --build --wait app
docker compose ps
curl --fail http://127.0.0.1:8501/_stcore/health
```

MiniLM is downloaded at image build time; Qwen is downloaded by the explicit pull
command. Both models remain on persistent volumes. The app waits for Ollama's API
to be healthy, but that health check does not verify that Qwen has been pulled.
The Streamlit health check verifies the web process, not the complete inference flow.

To test before setting up a domain, run this on your own computer, replacing
`user@server` with your SSH login:

```sh
ssh -N -L 8502:127.0.0.1:8501 user@server
```

Open `http://localhost:8502`. Check these flows:

- Assess “Early diabetic kidney disease can occur without symptoms.” with
  literature search disabled; confirm an assessment and evidence appear.
- Enable literature search and assess a claim with insufficient local evidence;
  confirm the search status, external evidence or fallback failure are visible.
- Save reviewer feedback and confirm it is written:

```sh
docker compose exec app python -c "from pathlib import Path; p=Path('/app/runtime/feedback.jsonl'); print('Feedback records:', len(p.read_text().splitlines()))"
```

The exact verdict can vary. An “assessment unavailable” result requires diagnosis
before publishing. Check `docker compose logs --tail=100 app ollama`. CPU inference
may exceed the 180-second per-request timeout; measure it before increasing the
timeout using `.env.deploy` below.

## Enable public HTTPS

Create a DNS A record for the hostname pointing to the server's public IPv4
address. If you add an AAAA record, it must point to working IPv6 on the same
server. Allow inbound ports 80/443 in the hosting provider's firewall.

```sh
cp .env.deploy.example .env.deploy
```

Edit `.env.deploy` and replace `glucotrust.example.com` with your actual hostname
(no `https://` prefix or path). Then run:

```sh
docker compose --env-file .env.deploy -f compose.yaml -f compose.https.yaml config --quiet
docker compose --env-file .env.deploy -f compose.yaml -f compose.https.yaml up -d --wait
```

Caddy obtains and renews HTTPS certificates once DNS and ports are ready; see
[Caddy's reverse proxy guide](https://caddyserver.com/docs/quick-starts/reverse-proxy).
Open `https://YOUR_HOSTNAME` and repeat the assessment and feedback checks. This
publishes the app to anyone with its URL; no sign-in is configured. Check Caddy
logs using the same Compose arguments followed by `logs --tail=100 caddy`.

On a hosted server, claims are processed on that server, not on each visitor's
computer. Assessment caches and feedback include claim text; enabled literature
search sends topic keywords to Europe PMC. Preserve the existing educational
prototype and no-personal-health-information notices.

## Persistence, updates, and rollback

The named volumes `ollama-models`, `app-cache`, and `feedback` keep model files,
assessment caches, and reviewer feedback across container replacement. HTTPS
uses two additional volumes for Caddy. Embedding arrays in `data/curated/` are
disposable and regenerate when a container is replaced. New Docker volumes copy
the image's initial cache contents; existing volumes keep their existing contents.
The app runs as a non-root user and writes feedback to
`GLUCOTRUST_FEEDBACK_PATH=/app/runtime/feedback.jsonl`.

Back up feedback to a file readable only by your account:

```sh
(umask 077; docker compose exec -T app cat /app/runtime/feedback.jsonl > feedback-backup.jsonl)
```

Use `docker compose stop` to stop without deleting data. Do not use
`docker compose down --volumes` unless you intend to delete the stored data.

Before an update, tag the working image:

```sh
docker image tag glucotrust-lite:local glucotrust-lite:previous
```

Copy the reviewed source update, then rebuild with `up -d --build --wait` using
the same Compose arguments as the active deployment. Repeat the smoke checks.
If assessment or feedback saving fails, restore the prior app image:

```sh
GLUCOTRUST_IMAGE_TAG=previous docker compose --env-file .env.deploy -f compose.yaml -f compose.https.yaml up -d --no-build --wait app
```

For private deployments, omit the environment-file and HTTPS override arguments.
Rollback changes the app image, not feedback or cache volumes. Retain the working
Ollama image; do not combine app updates with untested runtime/model upgrades.
The initial configuration uses moving upstream base/runtime image tags; record
their digests after a successful deployment before relying on reproducible rebuilds.
