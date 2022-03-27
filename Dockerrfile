FROM python:3.9-slim-bullseye

COPY ./src /myCVEs/src
COPY ./templates /myCVEs/templates

RUN pip install -r /myCVEs/src/requirements.txt 
RUN apt update
RUN apt-get -y install cron  && apt-get install vim -y
RUN echo "0 * * * * root python3 /myCVEs/src/main.py" >> /etc/crontab && echo "" >> /etc/crontab

CMD ["/bin/bash", "-c", "cron && tail -f /myCVEs/logs/mycves.log"]