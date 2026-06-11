API_DIR  := api
WEB_DIR  := web
RUN_DIR  := .run
API_PORT := 8000
WEB_PORT := 5173
PYTHON   := python3
MODEL    ?= lstm

.PHONY: help init up up-docker down clean restart logs test train

help: ## Muestra esta ayuda
	@echo "Targets disponibles:"
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed 's/:.*## /\t/' | sort

init: ## Instala dependencias de backend y frontend (una vez)
	cd $(API_DIR) && $(PYTHON) -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
	cd $(WEB_DIR) && npm install

up: up-docker ## Levanta la base de datos, backend y frontend en segundo plano
	@echo "Aplicando migraciones..."
	@cd $(API_DIR) && .venv/bin/alembic upgrade head
	@mkdir -p $(RUN_DIR)
	@( cd $(API_DIR) && MODEL=$(MODEL) exec .venv/bin/uvicorn main:app --port $(API_PORT) ) > $(RUN_DIR)/backend.log 2>&1 & echo $$! > $(RUN_DIR)/backend.pid
	@( cd $(WEB_DIR) && exec node_modules/.bin/vite --port $(WEB_PORT) ) > $(RUN_DIR)/frontend.log 2>&1 & echo $$! > $(RUN_DIR)/frontend.pid
	@echo "backend  → http://localhost:$(API_PORT)   (log: $(RUN_DIR)/backend.log)"
	@echo "frontend → http://localhost:$(WEB_PORT)   (log: $(RUN_DIR)/frontend.log)"

up-docker: ## Levanta la base de datos
	@echo "Levantando base de datos..."
	@sudo docker compose up -d --wait

down: ## Baja la base de datos, backend y frontend
	-@sudo docker compose down
	-@[ -f $(RUN_DIR)/backend.pid ]  && kill $$(cat $(RUN_DIR)/backend.pid)  2>/dev/null && echo "backend detenido"  || true
	-@[ -f $(RUN_DIR)/frontend.pid ] && kill $$(cat $(RUN_DIR)/frontend.pid) 2>/dev/null && echo "frontend detenido" || true
	-@rm -f $(RUN_DIR)/backend.pid $(RUN_DIR)/frontend.pid

clean: ## Detiene y elimina los contenedores, volúmenes de Docker
	-@sudo docker compose down -v

restart: down up ## Reinicia la base de datos, backend y frontend

logs: ## Sigue los logs de ambos procesos
	@tail -f $(RUN_DIR)/backend.log $(RUN_DIR)/frontend.log

test: ## Corre los tests del backend
	cd $(API_DIR) && PYTHONPATH=. .venv/bin/pytest -q

train: ## Entrena un modelo y guarda su artefacto (make train MODEL=xgboost; default lstm)
	cd $(API_DIR) && .venv/bin/python train.py --model $(MODEL)
