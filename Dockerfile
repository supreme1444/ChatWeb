FROM python:3.9.19

WORKDIR /code


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 127.0.0.1 --port 8000 --reload"]