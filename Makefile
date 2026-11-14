# Atajos. Toda la lógica vive en tareas.py para que funcione también sin make (Windows).
ifeq ($(OS),Windows_NT)
PY ?= py -3.11
else
PY ?= python3.11
endif

.PHONY: setup datos test eval demo

setup:
	$(PY) tareas.py setup

datos:
	$(PY) tareas.py datos

test:
	$(PY) tareas.py test

eval:
	$(PY) tareas.py eval

demo:
	$(PY) tareas.py demo
