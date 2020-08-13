FROM mitre/growthcleanr:latest

LABEL maintainer="Daniel Chudnov <dlchudnov@mitre.org>"

RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential

COPY . /app
COPY LICENSE /LICENSE
COPY README.md /README.md

RUN echo "Image built " > /app/templates/date.txt
RUN echo `date -u +"%c"` >> /app/templates/date.txt

WORKDIR /app

RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["app.py"]
