FROM python:3.11
WORKDIR /app
COPY . /app
ENV PYTHONPATH=$PYTHONPATH:/app/src/
RUN pip install -r requirements.txt
WORKDIR /app/src
# CMD python3 -m main.main lexecutor_all -c