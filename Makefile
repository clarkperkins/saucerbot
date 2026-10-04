
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
	uv run isort saucerbot tests

format/black:
	uv run black saucerbot tests

format: format/isort format/black

check/isort:
	uv run isort saucerbot --check

check/black:
	uv run black saucerbot --check

check/pylint:
	uv run pylint saucerbot --reports=n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"

check/mypy:
	uv run mypy saucerbot

check: check/isort check/black check/pylint check/mypy

staticfiles:
	uv run python manage.py collectstatic --noinput

test/pytest/xml: reports staticfiles
	uv run pytest --junit-xml=reports/tests/unit.xml --cov=saucerbot --cov-report=xml

test/pytest/html: reports staticfiles
	uv run pytest --cov=saucerbot --cov-report=html

test: test/pytest/xml

cov: test/pytest/html
	open reports/coverage/html/index.html

ci: check test
