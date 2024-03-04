FROM python:3.11

WORKDIR /wiki_generator
ENV PYTHONPATH /wiki_generator

RUN pip install --upgrade pip
COPY requirements/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && rm requirements.txt

COPY . .

EXPOSE 8006
CMD ["sh", "-c", "uvicorn --host 0.0.0.0 --port 8006 wiki_generator.main:app"]
