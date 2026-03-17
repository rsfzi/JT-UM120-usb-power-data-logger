# Development
Basic instructions: [https://packaging.python.org/en/latest/tutorials/packaging-projects/]

# Develop
1. git clone git@github.com:rsfzi/JT-UM120-usb-power-data-logger.git
1. python3 -m venv venv
1. venv/bin/pip install -e .[dev]

# Releasing
1. venv/bin/python -m build
1. venv/bin/twine upload [--repository testpypi] dist/*
