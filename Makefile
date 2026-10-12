PY ?= python
export PYTHONPATH := $(CURDIR)

.PHONY: sample install lock build prepare train index evaluate llm-eval feedback gate report test lint api api-dev web-install web-dev web-build demo
install:      ; $(PY) -m pip install -r requirements.lock
lock:         ; sh scripts/lock_requirements.sh $(PY)
build:        ; $(PY) -m src.cli build && $(PY) -m src.cli llm-eval && $(PY) -m src.cli report
prepare:      ; $(PY) -m src.cli prepare
train:        ; $(PY) -m src.cli train
index:        ; $(PY) -m src.cli index
evaluate:     ; $(PY) -m src.cli evaluate
llm-eval:     ; $(PY) -m src.cli llm-eval
feedback:     ; $(PY) -m src.cli feedback-loop
gate:         ; $(PY) -m src.cli quality-gate --with-tests
report:       ; $(PY) -m src.cli report && $(PY) scripts/build_docs.py
test:         ; $(PY) -m pytest
lint:         ; ruff check src tests scripts
api:          ; uvicorn src.main:app --host 127.0.0.1 --port 8000
api-dev:      ; SSA_DEV_MODE=1 uvicorn src.main:app --reload --reload-dir src --port 8000
web-install:  ; cd frontend && npm install
web-dev:      ; cd frontend && npm run dev
web-build:    ; cd frontend && npm run build
demo:         ; SSA_HOME=$(CURDIR)/.demo $(PY) -m src.cli demo-data && SSA_HOME=$(CURDIR)/.demo $(PY) -m src.cli build --no-dense
sample:       ; SSA_HOME=$(CURDIR)/.sample SSA_RAW_DIR=$(CURDIR)/data/sample_data $(PY) -m src.cli build --no-dense
