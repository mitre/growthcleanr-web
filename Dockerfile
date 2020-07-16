FROM mitre/growthcleanr:latest

MAINTAINER Daniel Chudnov "dlchudnov@mitre.org"

RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential

COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["app.py"]
