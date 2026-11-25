FROM python:3.12-slim

WORKDIR /app

# Only the pipeline code and the raw input data are needed to run it.
COPY src/ src/
COPY data/ data/

CMD ["python", "src/main.py"]
