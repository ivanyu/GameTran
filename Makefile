.PHONY: dist
dist: version.py
	uv run pyinstaller \
		--name=GameTran \
		--windowed \
		--icon=assets/icon.png \
		--add-data="assets/*:assets" \
		main.py
	$(eval VERSION := $(shell uv run version.py))
ifeq ($(OS),Windows_NT)
	@echo "Packaging for Windows"
	cd dist && 7z a GameTran-$(VERSION)-windows-x64.zip GameTran
else
	@echo "Packaging for Linux"
	tar -czvf dist/GameTran-$(VERSION)-linux-x64.tar.gz -C dist GameTran
endif

.PHONY: clean
clean:
	rm -rf build dist

.PHONY: version.py
version.py:
	uv run generate_version.py > version.py

.PHONY: format
format:
	uv run ruff check . --fix
