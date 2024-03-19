FROM python:3.12-slim-bookworm

WORKDIR /usr/src/app

ENV VIRTUAL_ENV=/usr/local
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

COPY engine/requirements.txt ./
RUN /root/.cargo/bin/uv pip install --no-cache-dir -r requirements.txt

COPY engine/ ./engine/
COPY shared/ ./shared/
COPY run.py ./run.py

VOLUME /usr/src/app/logs

CMD ["python", "run.py", "--docker"]