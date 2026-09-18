FROM python:3.11-slim

WORKDIR /app

# no BLAS/OpenMP bloat, keep image lean for CPU inference
ENV PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=4 \
    HF_HOME=/cache/huggingface

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8100
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100"]
