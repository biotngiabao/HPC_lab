Kubernetes deployment helper for lab4

This folder contains example Dockerfiles and Kubernetes manifests to deploy the components under `lab4/` to a Kubernetes cluster.

Overview
- `dockerfiles/` : Dockerfiles for `server`, `client`, `analysis` (build context should be `lab4`)
- `manifests/` : example Deployments, Services and a ConfigMap for `config.json`

Quick build examples (run from repository root):

1) Build images (example using tags):

```powershell
docker build -t myregistry/monitor-server:latest -f lab4/k8s/dockerfiles/server/Dockerfile lab4
docker build -t myregistry/monitor-client:latest -f lab4/k8s/dockerfiles/client/Dockerfile lab4
docker build -t myregistry/monitor-analysis:latest -f lab4/k8s/dockerfiles/analysis/Dockerfile lab4
```

Correct build contexts
----------------------

Docker's build `context` is the directory you pass as the last argument to `docker build`. Use one of these depending on where you run the commands from:

- From the `lab4/k8s` folder (`D:\Workspace\HPC_lab\lab4\k8s`):

```powershell
docker build -t lab4-base:latest -f dockerfiles/base/Dockerfile ..
docker build -t monitor-server:latest -f dockerfiles/server/Dockerfile ..
```

2) Push images to your registry:

```powershell
docker push myregistry/monitor-server:latest
docker push myregistry/monitor-client:latest
docker push myregistry/monitor-analysis:latest
```

3) Create ConfigMap from local `lab4/config.json` (or use the included manifest):

```powershell
kubectl create configmap lab4-config --from-file=lab4/config.json
```

4) Apply manifests:

```powershell
kubectl apply -f lab4/k8s/manifests/
```

Notes
- Replace `myregistry/...` with your registry (Docker Hub, GHCR, GCR, etc.).
- For local clusters (kind/minikube) you can `kind load docker-image` or `minikube image load` instead of pushing.
- Adjust resource, probe, and env values in manifests to suit your environment.

Troubleshooting: base image and Skaffold
--------------------------------------

- Skaffold normally builds all images listed in `skaffold.yaml`. If a service Dockerfile references `FROM lab4-base:latest`, Docker may try to pull `lab4-base:latest` from a registry when the local builder cannot see the freshly-built base image. Ways to avoid this:
	- Ensure `skaffold.yaml` uses `useDockerCLI: true` and a `tagPolicy` that produces `:latest` tags (this repo config does this).
	- Build the base image manually first so `lab4-base:latest` exists in your local daemon:

```powershell
# from repo root
docker build -t lab4-base:latest -f lab4/k8s/dockerfiles/base/Dockerfile lab4
```

- Or let Skaffold build and then load images into the cluster (useful for `kind`/`minikube`):

```powershell
skaffold build
# for kind
kind load docker-image lab4-base:latest
kind load docker-image monitor-server:latest
# for minikube
minikube image load lab4-base:latest
```

Skaffold (local dev)
--------------------

This repository includes a `skaffold.yaml` in this folder to simplify local development and deployment.

Quick start (from repository root):

```powershell
cd lab4/k8s
# Run Skaffold in development mode (rebuilds on change, applies manifests)
skaffold dev

# Or run once (build images and apply manifests):
skaffold run

# To delete deployed resources created by Skaffold:
skaffold delete
```

Profiles:
- `kind`: use when deploying to a `kind` cluster. Example: `skaffold dev -p kind`
- `minikube`: use when deploying to `minikube`. Example: `skaffold dev -p minikube`

Notes:
- By default Skaffold builds images into your local Docker daemon (no push). For kind/minikube you can load images to the cluster or use the provided profiles.
- Update image names in `skaffold.yaml` or manifests to match your registry if you want to push images instead of building locally.

Base image optimization
-----------------------

This layout uses a shared base image `lab4-base` which pre-installs system build dependencies and all Python requirements. Advantages:

- Faster incremental builds for `server`, `client`, and `analysis` because only application code is copied after the base image is built.
- Avoids repeating heavy pip installs in each service image.

Skaffold will build `lab4-base` first (it's included as the first artifact). If you change `requirements.txt`, re-run `skaffold run` or `skaffold dev` so the base image is rebuilt.


