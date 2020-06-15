git_commit := $(shell git rev-parse HEAD)
build_date := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')

clean:
	rm -rf .coverage .mypy_cache .pytest_cache reports staticfiles

build/docker:
	docker build --pull --build-arg GIT_COMMIT=$(git_commit) --build-arg BUILD_DATE=$(build_date) --tag clarkperkins/saucerbot .

build: build/docker

reports:
	mkdir -p reports

check/pycodestyle:
	pycodestyle saucerbot

check/pylint: reports
	pylint saucerbot --reports=n --exit-zero --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint.txt

check/mypy:
	mypy saucerbot

check: check/pycodestyle check/pylint check/mypy

test/pytest/xml: reports
	DJANGO_ENV=test pytest --cov=saucerbot --cov-report=xml

test/pytest/html: reports
	DJANGO_ENV=test pytest --cov=saucerbot --cov-report=html

test: test/pytest/xml

cov: test/pytest/html
	open reports/html/index.html

ci: build check test