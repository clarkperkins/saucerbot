FROM python:3.7-alpine

RUN apk add gcc g++ linux-headers postgresql-dev

RUN pip install twine

RUN mkdir -p /build/wheels

WORKDIR /build/wheels

CMD pip wheel $PACKAGES && twine upload --repository-url https://push.fury.io/clarkperkins/ -u $FURY_TOKEN -p '' *-cp37-cp37m-linux_x86_64.whl
