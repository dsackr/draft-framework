FROM python:3.11-slim

WORKDIR /srv/draft

RUN apt-get update \
  && apt-get install -y --no-install-recommends git \
  && rm -rf /var/lib/apt/lists/*

COPY app/api/requirements.txt app/api/requirements.txt
RUN python -m pip install --no-cache-dir -r app/api/requirements.txt

COPY app app
COPY framework framework

ENV DRAFT_WORKSPACE=/workspace
EXPOSE 8000

CMD ["uvicorn", "draft_app.main:app", "--app-dir", "app/api", "--host", "0.0.0.0", "--port", "8000"]
