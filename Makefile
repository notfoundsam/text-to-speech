# Text-to-Speech - Makefile
# Usage: make <target>

.PHONY: build lint fix clean help

# Default target
.DEFAULT_GOAL := help

# Configuration
COMPOSE = docker compose
SERVICE = tts
RUFF_VERSION = 0.9.7

## build: Build Docker image
build:
	DOCKER_BUILDKIT=1 $(COMPOSE) build

## lint: Run Ruff linter and format check
lint:
	$(COMPOSE) run --rm --no-deps --entrypoint sh $(SERVICE) -c \
		"pip install -q --root-user-action=ignore ruff==$(RUFF_VERSION) && ruff check tts_app/ && ruff format --check tts_app/"

## fix: Auto-fix lint issues and format code
fix:
	$(COMPOSE) run --rm --no-deps --entrypoint sh $(SERVICE) -c \
		"pip install -q --root-user-action=ignore ruff==$(RUFF_VERSION) && ruff check --fix tts_app/ && ruff format tts_app/"

## clean: Remove generated chunks and output files
clean:
	rm -rf data/chunks/* data/output/*
	@echo "Chunks and output files removed"

## help: Show this help message
help:
	@echo "Text-to-Speech - Available Commands:"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'
	@echo ""
