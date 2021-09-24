FROM python:3.9-alpine
ENV prometheus_multiproc_dir=multiproc-tmp

ARG APPDIR=/app/
COPY requirements.txt $APPDIR
RUN apk add --no-cache --virtual .build-deps \
		gcc \
		libc-dev \
		linux-headers \
		libffi-dev \
		openssl-dev \
		python3-dev && \
	pip install -r /app/requirements.txt &&  \
	apk del .build-deps && \
	mkdir $APPDIR$prometheus_multiproc_dir

COPY . $APPDIR

WORKDIR $APPDIR

ENV PYTHONUNBUFFERED=1

EXPOSE 9100
ENTRYPOINT python manage.py run_hueyx_prometheus --port 9100

#EXPOSE 8000
#ENTRYPOINT python manage.py migrate && python manage.py runserver 0.0.0.0:8000 --noreload

