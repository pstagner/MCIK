# Makefile for MCIK (MicroCause Intrinsic Kernels) Project
# This provides convenient targets for building, testing, and running various components

.PHONY: help install-deps install-python-deps clean test build-cmake run-analysis-5min run-analysis-daily

# Default target
help:
	@echo "MCIK (MicroCause Intrinsic Kernels) Project"
	@echo ""
	@echo "Available targets:"
	@echo "  help                - Show this help message"
	@echo "  install-deps        - Install all system and Python dependencies"
	@echo "  install-python-deps - Install only Python dependencies"
	@echo "  clean               - Clean build artifacts and caches"
	@echo "  test                - Run pytest suite (Python)"
	@echo "  test-install        - Test that the installation is working correctly"
	@echo "  build-cmake         - Configure and build C++ targets (mcik_demo, ascii_torus)"
	@echo "  run-analysis-5min   - Run 5-minute interval stock sensitivity analysis"
	@echo "  run-analysis-daily  - Run daily interval stock sensitivity analysis"
	@echo ""
	@echo "For detailed usage, see the README files in each experiment directory."

# Install all dependencies (system + Python)
install-deps: install-python-deps
	@echo "Installing system dependencies..."
	@if [ -f "experiments/etflevels-3dVisQuantitiveDataAnalysis/install_dependencies.sh" ]; then \
		cd experiments/etflevels-3dVisQuantitiveDataAnalysis && ./install_dependencies.sh; \
	else \
		echo "System dependencies script not found. Install manually:"; \
		echo "  sudo apt update"; \
		echo "  sudo apt install postgresql-client postgresql-server-dev-all build-essential python3-dev"; \
		echo "  sudo apt install libfreetype6-dev libpng-dev libffi-dev libssl-dev"; \
	fi

# Install only Python dependencies
install-python-deps:
	@echo "Installing Python dependencies..."
	@find . -name "requirements.txt" -exec echo "Installing from {}" \; -exec pip install -r {} \;

# Clean build artifacts and Python caches
clean:
	@echo "Cleaning build artifacts and caches..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ *.egg-info 2>/dev/null || true
	@rm -rf experiments/*/build/ 2>/dev/null || true
	@echo "Clean complete."

# Run tests
test:
	@echo "Running pytest suite..."
	@python -m pytest tests -v

# Test installation
test-install:
	@echo "Testing installation..."
	@if [ -f "experiments/etflevels-3dVisQuantitiveDataAnalysis/test_installation.py" ]; then \
		cd experiments/etflevels-3dVisQuantitiveDataAnalysis && python test_installation.py; \
	else \
		echo "Installation test script not found."; \
	fi

# Build C++ components with CMake
build-cmake:
	@echo "Building C++ components with CMake..."
	@if [ -f "CMakeLists.txt" ]; then \
		mkdir -p build && cd build && cmake .. && cmake --build . --target mcik_demo ascii_torus; \
	else \
		echo "No CMakeLists.txt found in project root."; \
	fi

# Run 5-minute interval stock sensitivity analysis
run-analysis-5min:
	@echo "Running 5-minute interval stock sensitivity analysis..."
	@if [ -f "experiments/etflevels-3dVisQuantitiveDataAnalysis/visualize_stock_sensitivity.py" ]; then \
		cd experiments/etflevels-3dVisQuantitiveDataAnalysis && python ./visualize_stock_sensitivity.py; \
	else \
		echo "5-minute analysis script not found."; \
	fi

# Run daily interval stock sensitivity analysis (if different script exists)
run-analysis-daily:
	@echo "Running daily interval stock sensitivity analysis..."
	@echo "Note: This requires a different script or configuration for daily data"
	@echo "Check experiments/etflevels-dVisQuantitiveDataAnalysis/ for daily analysis"

# Install and run 5-minute analysis in one command
quick-start-5min: install-deps run-analysis-5min

# Show system information
info:
	@echo "=== System Information ==="
	@echo "Python version: $(shell python --version 2>/dev/null || python3 --version)"
	@echo "Pip version: $(shell pip --version 2>/dev/null || pip3 --version)"
	@echo ""
	@echo "=== Project Structure ==="
	@find experiments -name "*.py" -o -name "*.cpp" -o -name "*.hpp" | head -20
	@echo ""
	@echo "=== GPU Information ==="
	@nvidia-smi --query-gpu=name,memory.total,memory.free,memory.used --format=csv,noheader,nounits 2>/dev/null || echo "No NVIDIA GPU detected or nvidia-smi not available"

# Database setup helper
setup-db:
	@echo "=== Database Setup ==="
	@echo "Make sure PostgreSQL is running:"
	@echo "  sudo systemctl start postgresql  # or service postgresql start"
	@echo ""
	@echo "Create database:"
	@echo "  sudo -u postgres createdb postgres"
	@echo "  sudo -u postgres psql -c \"CREATE USER postgres WITH PASSWORD 'postgres';\""
	@echo "  sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;\""
	@echo ""
	@echo "Import your stock data into a table named 'prices' with columns:"
	@echo "  ts (timestamp), symbol (text), open (numeric), high (numeric),"
	@echo "  low (numeric), close (numeric), volume (numeric)"
