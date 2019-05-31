FROM python:3.6
ENV PYTHONUNBUFFERED 1
ARG ENV
ADD requirements/common.txt /
ADD requirements/$ENV.txt /
RUN pip install -r /$ENV.txt; mkdir /src;
COPY ./src /src
WORKDIR /src