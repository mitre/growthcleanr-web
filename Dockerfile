FROM mitre/growthcleanr:latest

LABEL maintainer="Daniel Chudnov <dlchudnov@mitre.org>"

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip

COPY . /app
COPY LICENSE /LICENSE
COPY README.md /README.md

RUN echo "Image built " > /app/templates/date.txt
RUN echo `date -u +"%c"` >> /app/templates/date.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

RUN addgroup --gid 1202 gcuser && adduser --system --uid 1002 --ingroup gcuser gcuser
RUN chown -R gcuser:gcuser /app

USER gcuser

ENTRYPOINT ["python3"]
CMD ["app.py"]
