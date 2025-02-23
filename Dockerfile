FROM docker.io/continuumio/miniconda3:latest

RUN useradd -m app

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY --chown=app:app ./src /opt/app
COPY --chown=app:app ./.streamlit /opt/app/.streamlit

WORKDIR /opt/app
USER app
