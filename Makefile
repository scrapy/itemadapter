.PHONY: lint types black

lint:
	@python -m flake8 --exclude=.git,venv* scrapy_itemadapter.py tests

types:
	@mypy --ignore-missing-imports --follow-imports=skip scrapy_itemadapter.py

black:
	@black --check scrapy_itemadapter.py tests
