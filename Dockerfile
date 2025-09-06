FROM python:3.9-alpine
LABEL maintainer="Hannes Moehring"

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install "pip==21.3"
COPY . .



RUN pip install "torch==1.11.0 torchmetrics==0.7.2 torchvision==0.12.0 numpy==1.22.3"

RUN pip install "chumpy==0.70" --no-build-isolation
RUN pip install "grpcio --only-binary=grpcio"
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "api_handler.py"]