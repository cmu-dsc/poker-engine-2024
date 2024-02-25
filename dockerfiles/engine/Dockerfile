FROM python:3.12-alpine

WORKDIR /usr/src/app

ENV VIRTUAL_ENV=/usr/local
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

COPY engine/requirements.txt ./
RUN /root/.cargo/bin/uv pip install --no-cache-dir -r requirements.txt

COPY engine/ ./engine/

COPY shared/ ./shared/

EXPOSE 50051

CMD ["python", "engine/engine.py"]
