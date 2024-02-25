FROM python:3.12-alpine

WORKDIR /usr/src/app

RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev && pip install --no-cache-dir Cython

COPY engine/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY engine/ ./engine/

COPY shared/ ./shared/

EXPOSE 50051

CMD ["python", "engine/engine.py"]
