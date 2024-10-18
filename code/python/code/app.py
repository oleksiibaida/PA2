import sys
import asyncio
import threading
from queue import Queue
from mqtt import MqttBroker
from tg_bot import Bot
telegram_token = '7599050852:AAHa5HvtMA046Vnb3vcDvBA_5AUgvplQ-RQ'

hostname = '192.168.1.10'
port=1883
topic=['alarm','haha']
client_id="myid"



def main():
    q = Queue()

    mqtt_broker = MqttBroker(q,hostname,port,topic,client_id)
    mqtt_broker.run()

    tg_bot = Bot(q,telegram_token)
    tg_bot.run()

    mqtt_broker.join()
    tg_bot.join()

if __name__=="__main__":
    main()