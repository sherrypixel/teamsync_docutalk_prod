FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --upgrade pip

RUN pip install -r /code/requirements.txt

COPY ./app /code/app

RUN python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords')"

CMD [ "python", "app/main.py"]