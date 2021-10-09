git_commit := $(shell git rev-parse HEAD)
build_date := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')

clean:
	rm -rf .coverage .mypy_cache .pytest_cache reports staticfiles build dist

build/docker:
	docker build --pull --build-arg GIT_COMMIT=$(git_commit) --build-arg BUILD_DATE=$(build_date) --tag clarkperkins/saucerbot .

build: build/docker

reports:
	mkdir -p reports

format/isort:
	isort saucerbot tests

format/black:
	black saucerbot tests

format: format/isort format/black

check/isort:
	isort saucerbot --check

check/black:
	black saucerbot --check

check/pylint: reports
	pylint saucerbot --reports=n --exit-zero --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint.txt

check/mypy:
	mypy saucerbot

check: check/isort check/black check/pylint check/mypy

staticfiles:
	python manage.py collectstatic --noinput

test/pytest/xml: reports staticfiles
	pytest --cov=saucerbot --cov-report=xml

test/pytest/html: reports staticfiles
	pytest --cov=saucerbot --cov-report=html

test: test/pytest/xml

cov: test/pytest/html
	open reports/html/index.html

integration-test/pytest/xml: reports
	pytest -m integration --cov=saucerbot --cov-report=xml --cov-append

integration-test/pytest/html: reports
	pytest -m integration --cov=saucerbot --cov-report=html --cov-append

integration-test: integration-test/pytest/xml

sonar: check/pylint test/pytest/xml integration-test/pytest/xml
	sonar-scanner

ci: check test integration-test sonar
