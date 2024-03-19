FROM python:3.12-bookworm

WORKDIR /usr/src/app

ENV VIRTUAL_ENV=/usr/local
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

ENV UV_HTTP_TIMEOUT 600

COPY shared/ ./shared/

COPY python_skeleton/requirements.txt ./
RUN /root/.cargo/bin/uv pip install --no-cache-dir -r requirements.txt

COPY python_skeleton/ ./python_skeleton/

EXPOSE 50051

CMD ["python", "python_skeleton/prob_bot.py"]