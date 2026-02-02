.PHONY: help install install-deps install-service uninstall enable disable start stop restart status logs clean

SYSTEMD_USER_DIR := $(HOME)/.config/systemd/user
CONFIG_DIR := $(HOME)/.config/screenwatch
PIPX := $(shell command -v pipx 2> /dev/null)

help:
	@echo "Screenwatch - Screen connection monitor"
	@echo ""
	@echo "Available targets:"
	@echo "  install           - Install everything (dependencies + service)"
	@echo "  install-deps      - Install Python package with pipx"
	@echo "  install-service   - Install systemd service file"
	@echo "  uninstall         - Remove package and service"
	@echo "  enable            - Enable systemd service"
	@echo "  disable           - Disable systemd service"
	@echo "  start             - Start the service"
	@echo "  stop              - Stop the service"
	@echo "  restart           - Restart the service"
	@echo "  status            - Show service status"
	@echo "  logs              - Show service logs"
	@echo "  clean             - Remove build artifacts"

check-pipx:
ifndef PIPX
	@echo "Error: pipx is not installed"
	@echo "Please install pipx first:"
	@echo "  - Debian/Ubuntu: sudo apt install pipx"
	@echo "  - Fedora: sudo dnf install pipx"
	@echo "  - Arch: sudo pacman -S python-pipx"
	@echo "  - Or use pip: pip install --user pipx"
	@exit 1
endif

install-deps: check-pipx
	@echo "Installing screenwatch with pipx..."
	pipx install .
	@echo "Installation complete!"

install-service:
	@echo "Installing systemd service..."
	mkdir -p $(SYSTEMD_USER_DIR)
	cp screenwatch.service $(SYSTEMD_USER_DIR)/
	systemctl --user daemon-reload
	@echo "Service installed to $(SYSTEMD_USER_DIR)/screenwatch.service"
	@echo ""
	@echo "You may want to copy the example config:"
	@mkdir -p $(CONFIG_DIR)
	@if [ ! -f $(CONFIG_DIR)/config.ini ]; then \
		cp config.ini.example $(CONFIG_DIR)/config.ini; \
		echo "Created default config at $(CONFIG_DIR)/config.ini"; \
	else \
		echo "Config already exists at $(CONFIG_DIR)/config.ini"; \
	fi

install: install-deps install-service
	@echo ""
	@echo "Installation complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit config (optional): $(CONFIG_DIR)/config.ini"
	@echo "  2. Enable service: make enable"
	@echo "  3. Start service: make start"
	@echo "  4. Check status: make status"

uninstall: stop disable
	@echo "Uninstalling screenwatch..."
	-pipx uninstall screenwatch 2>/dev/null || true
	rm -f $(SYSTEMD_USER_DIR)/screenwatch.service
	systemctl --user daemon-reload
	@echo "Uninstalled (config kept in $(CONFIG_DIR))"

enable:
	systemctl --user enable screenwatch.service
	@echo "Service enabled (will start on login)"

disable:
	systemctl --user disable screenwatch.service
	@echo "Service disabled"

start:
	systemctl --user start screenwatch.service
	@echo "Service started"

stop:
	-systemctl --user stop screenwatch.service
	@echo "Service stopped"

restart: stop start

status:
	systemctl --user status screenwatch.service

logs:
	journalctl --user -u screenwatch.service -f

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
