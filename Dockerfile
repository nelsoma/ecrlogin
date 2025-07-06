FROM alpine:3

COPY create_ecr_secret.py /root/python/create_ecr_secret.py
COPY requirements.txt /root/python/requirements.txt
RUN apk add --update --no-cache python3 py3-pip && \
    pip3 install --upgrade pip --break-system-packages && \
    pip3 install -r /root/python/requirements.txt --break-system-packages && \
    rm -rf /var/cache/apk/* && \
    rm -rf /root/python/__pycache__
WORKDIR /root/python/

CMD  ["python3", "create_ecr_secret.py"]