FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY . .

FROM python:3.11-slim

RUN groupadd --system --gid 1001 adcleaner && \
    useradd --system --uid 1001 --gid adcleaner adcleaner

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app .

RUN chown -R adcleaner:adcleaner /app

USER adcleaner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

COPY entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh
USER adcleaner

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "app.main"]
