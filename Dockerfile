FROM python:3.10
RUN apt-get update && apt-get -y install cron vim
WORKDIR /app
ENV TZ Asia/Bangkok

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN pip install --upgrade cython
RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y cron vim
RUN apt-get install -y gnupg2
RUN apt-get install -y curl apt-transport-https
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

COPY . .
COPY crontab /etc/cron.d/crontab

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab


# run crond as main process of container
CMD ["cron", "-f"]