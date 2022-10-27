
clean:
	rm -rf .coverage .mypy_cache .pytest_cache reports staticfiles build dist

build/docker:
	docker build --pull --tag clarkperkins/saucerbot .

build: build/docker

reports:
	mkdir -p reports
	mkdir -p reports/coverage
	mkdir -p reports/tests

format/isort:
	poetry run isort saucerbot tests

format/black:
	poetry run black saucerbot tests

format: format/isort format/black

check/isort:
	poetry run isort saucerbot --check

check/black:
	poetry run black saucerbot --check

check/pylint: reports
	poetry run pylint saucerbot --reports=n --exit-zero --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint.txt

check/mypy:
	poetry run mypy saucerbot

check: check/isort check/black check/pylint check/mypy

staticfiles:
	poetry run python manage.py collectstatic --noinput

test/pytest/xml: reports staticfiles
	poetry run pytest --junit-xml=reports/tests/unit.xml --cov=saucerbot --cov-report=xml

test/pytest/html: reports staticfiles
	poetry run pytest --cov=saucerbot --cov-report=html

test: test/pytest/xml

cov: test/pytest/html
	open reports/coverage/html/index.html

sonar: check/pylint test/pytest/xml
	sonar-scanner

ci: check test sonar
