FROM python:3.9

# os setup
RUN apt-get update
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Copy settings
COPY docker/datadoggie/settings.py /usr/src/app/settings.py

# install requirements
COPY datadoggie/requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# move codebase over
COPY datadoggie /usr/src/app

# run command
CMD ["python", "histogram_server.py", "run"]