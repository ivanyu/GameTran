.PHONY: dist
dist:
	@echo "Generating version.py..."
	python3 build_version.py
	@echo "Building distribution..."
	uv run pyinstaller \
		--icon=assets/icon.png \
		--add-data="assets/*:assets" \
		main.py

.PHONY: format
format:
	uv run ruff check . --fix

.PHONY: version.py
version.py:
	uv run generate_version.py > version.py
