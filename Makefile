# Define variables for the virtual environment directory
VENV = env
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Create the virtual environment
$(VENV):
	python3 -m venv $(VENV)

# Install Python dependencies
install-py: $(VENV)
	$(PIP) install -r requirements.txt

# Install NPM dependencies
install-npm:
	npm install

# Run Percy tests
test: $(VENV)
	npx percy exec -- $(PYTHON) tests/automate/test.py
