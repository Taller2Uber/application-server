FROM ubuntu:latest
MAINTAINER fncaldora "facundo.caldora@gmail.com"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /llevame
WORKDIR /llevame
RUN pip install -r requirements.txt
RUN useradd -m myuser
USER myuser
CMD gunicorn --bind 0.0.0.0:$PORT llevame:app


