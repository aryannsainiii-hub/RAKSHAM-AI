FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./pyproject.toml
COPY app ./app
RUN pip install --no-cache-dir .
ENV RAKSHAM_DB_PATH=/data/raksham.sqlite3
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
