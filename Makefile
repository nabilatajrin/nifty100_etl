# ============================================================
# Makefile — NIFTY 100 ETL Capstone
# Shortcuts for common project commands.
# Run a target with:  make <target>   (e.g. make load)
# ============================================================

# Use the project's virtual-environment Python
PYTHON = python

.PHONY: help load ratios test report dashboard api clean

help:
	@echo "Available commands:"
	@echo "  make load       - Run the ETL pipeline (load all source files into the DB)"
	@echo "  make ratios      - Compute financial ratios"
	@echo "  make test        - Run the unit test suite with pytest"
	@echo "  make report      - Generate the analysis report"
	@echo "  make dashboard   - Launch the Streamlit dashboard"
	@echo "  make api         - Start the API server"
	@echo "  make clean       - Remove generated files (db, caches, outputs)"

load:
	$(PYTHON) -m src.etl.db_loader

ratios:
	$(PYTHON) -m src.analytics.compute_ratios

test:
	pytest tests/ -v

report:
	$(PYTHON) -m src.analytics.capital_allocation_report

dashboard:
	streamlit run src/dashboard/app.py

api:
	$(PYTHON) -m src.api.main

clean:
	rm -f data/*.db
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -f output/*.csv
	@echo "Cleaned generated files."
