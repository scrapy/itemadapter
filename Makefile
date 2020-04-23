.PHONY: lint types black clean

lint:
	@python -m flake8 --exclude=.git,venv* itemadapter tests

types:
	@mypy --ignore-missing-imports --follow-imports=skip itemadapter

black:
	@black --check itemadapter tests

clean:
	@find . -name "*.pyc" -delete
	@rm -rf .mypy_cache/ .tox/ build/ dist/ htmlcov/ .coverage coverage.xml
