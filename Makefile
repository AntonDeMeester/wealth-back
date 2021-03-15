PYTHON_FOLDERS := wealth tests

check:
	mypy ${PYTHON_FOLDERS}
	pylint  ${PYTHON_FOLDERS} --fail-under 9
	radon cc  ${PYTHON_FOLDERS} -a -nc

reformat:
	isort  ${PYTHON_FOLDERS}
	black  ${PYTHON_FOLDERS}

check-reformat:
	isort --check-only  ${PYTHON_FOLDERS}
	black --check  ${PYTHON_FOLDERS}

test:
	pytest --cov=wealth --cov-report term --cov-report html:coverage\/cov_html tests

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr coverage/
	rm -fr .pytest_cache

run:
	uvicorn wealth.main:app

run-dev:
	uvicorn wealth.main:app --reload