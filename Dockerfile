FROM python:3.7-alpine
ENV prometheus_multiproc_dir=multiproc-tmp

ARG APPDIR=/app/
COPY requirements.txt $APPDIR
COPY requirements_sidecar.txt $APPDIR
RUN apk add --no-cache --virtual .build-deps \
		gcc \
		libc-dev \
		linux-headers && \
	pip install -r /app/requirements.txt &&  \
	pip install -r /app/requirements_sidecar.txt &&  \
	apk del .build-deps && \
	mkdir $APPDIR$prometheus_multiproc_dir

COPY . $APPDIR

WORKDIR $APPDIR

ENV PYTHONUNBUFFERED=1

EXPOSE 9100
ENTRYPOINT python manage.py run_hueyx_prometheus --port 9100

#EXPOSE 8000
#ENTRYPOINT python manage.py migrate && python manage.py runserver 0.0.0.0:8000 --noreload

