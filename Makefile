# Makefile
.PHONY: help up down clean reload

help:
	@echo "Available commands:"
	@echo "  make up      - Build and start the system"
	@echo "  make down    - Stop the system"
	@echo "  make clean   - Stop and remove volumes (Wipes DB)"
	@echo "  make reload  - Wipe DB, rebuild, and restart (Fresh Start)"

up:
	docker-compose up --build

down:
	docker-compose down

clean:
	docker-compose down -v

reload: clean up