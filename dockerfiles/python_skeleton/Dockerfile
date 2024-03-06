FROM python:3.12-alpine

WORKDIR /usr/src/app

ENV VIRTUAL_ENV=/usr/local
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

COPY python_skeleton/requirements.txt ./
RUN /root/.cargo/bin/uv pip install --no-cache-dir -r requirements.txt
RUN /root/.cargo/bin/uv pip install -e .

COPY python_skeleton/ ./python_skeleton/

COPY shared/ ./shared/

EXPOSE 50051

CMD ["python", "python_skeleton/player.py"]