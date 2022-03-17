FROM python:3.8
WORKDIR /usr/src/ali

COPY aligrabber.py id_posts.txt config.json ./

RUN pip install pyTelegramBotAPI telebot
RUN pip install admitad vk

CMD python aligrabber.py

