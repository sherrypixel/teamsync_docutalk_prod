FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --upgrade pip

RUN pip install -r /code/requirements.txt

COPY ./app /code/app

CMD [ "python", "app/main.py"]