install:
	poetry install

project:
	poetry run python main.py

build:
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install dist/*.whl --force-reinstall --no-deps

lint:
	poetry run ruff check .