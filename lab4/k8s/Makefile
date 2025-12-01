SHELL := /bin/bash

# Build context: parent directory (lab4)
CONTEXT := ..

.PHONY: help build-base build-server build-client build-analysis build-all skaffold-run run build-and-load-kind clean

help:
	@echo "Makefile targets for lab4/k8s"
	@echo
	@echo "  make build-base           # build lab4-base:latest"
	@echo "  make build-server         # build monitor-server:latest"
	@echo "  make build-client         # build monitor-client:latest"
	@echo "  make build-analysis       # build monitor-analysis:latest"
	@echo "  make build-all            # build base + all services"
	@echo "  make run                 # build base then skaffold run"
	@echo "  make skaffold-run         # run 'skaffold run' (deploy via skaffold)"
	@echo "  make build-and-load-kind  # build all images and load them into kind, then apply manifests"
	@echo

build-base:
	@echo "Building lab4-base:latest (context: $(CONTEXT))"
	docker build -t lab4-base:latest -f dockerfiles/base/Dockerfile $(CONTEXT)

build-server:
	@echo "Building monitor-server:latest"
	docker build -t monitor-server:latest -f dockerfiles/server/Dockerfile $(CONTEXT)

build-client:
	@echo "Building monitor-client:latest"
	docker build -t monitor-client:latest -f dockerfiles/client/Dockerfile $(CONTEXT)

build-analysis:
	@echo "Building monitor-analysis:latest"
	docker build -t monitor-analysis:latest -f dockerfiles/analysis/Dockerfile $(CONTEXT)

build-all: build-base build-server build-client build-analysis

skaffold-run:
	@echo "Running: skaffold run"
	skaffold run

dev:
	@echo "Running: skaffold dev (blocking)"
	skaffold dev

stop:
	@echo "Stopping Skaffold and deleting deployed resources (if any)"
	-@skaffold delete || true
	-@pkill -f skaffold || true

run: build-base skaffold-run

build-and-load-kind: build-all
	@echo "Loading images into kind and applying manifests..."
	-kind load docker-image lab4-base:latest || true
	-kind load docker-image monitor-server:latest || true
	-kind load docker-image monitor-client:latest || true
	-kind load docker-image monitor-analysis:latest || true
	-kubectl apply -f manifests/

clean:
	@echo "No-op: remove locally built images if desired"
	@echo "  docker rmi lab4-base:latest monitor-server:latest monitor-client:latest monitor-analysis:latest"
