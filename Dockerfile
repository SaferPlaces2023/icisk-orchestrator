FROM python:3.10-slim

# WORKDIR /notebook

RUN pip install jupyter jupyter_client nbformat

# CMD ["jupyter-notebook"]