FROM python:3.11-slim

# WORKDIR /notebook
COPY . /app
WORKDIR /app

RUN pip install .
# RUN pip install -U "langgraph-cli[inmem]"
EXPOSE 2024

CMD ["python","/app/src/launch.py"]