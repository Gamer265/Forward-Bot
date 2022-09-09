FROM python:3.10.4-slim-buster
COPY . /bot
WORKDIR /bot
RUN pip3 install -r requirements.txt
CMD ["bash", "run.sh"]
