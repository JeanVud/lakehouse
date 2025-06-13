FROM python:3.12

RUN pip install fastapi[standard]

COPY app /app

USER daemon

CMD [ "sleep", "infinity" ]