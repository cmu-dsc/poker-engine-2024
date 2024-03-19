FROM python:3.12-alpine

WORKDIR /usr/src/app

COPY engine/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/

COPY engine/ ./engine/

COPY run.py ./run.py

VOLUME /usr/src/app/logs

CMD ["python", "run.py", "--docker"]