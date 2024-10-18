from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, error
from telegram.ext import Updater, filters, ConversationHandler, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackContext
import threading
import json
import db
from queue import Queue, Empty


class Bot(threading.Thread):
    def __init__(self,queue,token):
        threading.Thread.__init__(self)
        self.token = token
        self.queue = queue
        self.db_json = 'include/users.json'

        # Verbidnung zum DB
        self.db = db.Datenbank()

    
    def get_db_json(self):
        try:
            with open(self.db_json, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}


    async def command_start(self, update:Update, context:CallbackContext):
        self.chat_id = update.effective_chat.id
        print('Chatid: ',self.chat_id)
        print('Fullname: ', update.effective_chat.full_name)
        print('USername: ',update.effective_user.name)
        print('UserID ', update.effective_user.to_dict())
        self.db.add_user(update.effective_user.to_dict())
        print("get user data")
        get_user_data = self.db.get_user_data_db(id=update.effective_user.id)
        print(get_user_data['id'],' GET ',get_user_data['first_name'])
        await self.application.bot.send_message(self.chat_id,"STARTing this bot")

    async def send_message(self, text):
        print('TG-BOT: Nachricht senden in TG:\n', text)
        await self.application.bot.send_message(self.chat_id,text)

    async def wait_mqtt_message(self, context:CallbackContext):
        try:
            mqtt_message = self.queue.get_nowait()  # Thread-safe
            print(f"TG-BOT: Erhalten mqtt-message: Topic: {mqtt_message['topic']}, text: {mqtt_message['text']}")
            if self.chat_id:
                # MQTT-Nachricht verarbeiten
                await self.handle_mqtt_message(mqtt_message)
            self.queue.task_done()
        except Empty:
            # Keine Nachricten in Queue
            pass

    async def handle_mqtt_message(self, mqtt_message):
        if mqtt_message['topic'] == "alarm":
            if mqtt_message['text'] == 'fire_start':
                await self.send_message("🔥ALARM🔥\nFEUER\n")
            elif mqtt_message['text'] == 'gas_start':
                await self.send_message("💨ALARM💨\nGAS\n")
                print("SENT TG MES")
            elif mqtt_message['text'] == 'pir_move':
                await self.send_message("🥷ALARM🥷\nFremdbewegung Erkannt\nAlarm einschalten?")
                #TODO Turn on Alarm
            elif mqtt_message['text'] == 'pin_wrong':
                await self.send_message("🔒ALARM🔒\nFalsche PIN wurde eingegeben!\n Alarm einschalten?")
                print("SENT TG MES")
        elif mqtt_message['topic'] == "status":
            if mqtt_message['text'] == 'pinchanged':
                await self.send_message("Neue PIN eingegeben")
            elif mqtt_message['text'] == 'feuer':
                await self.send_message('status feuer')

    async def test(self, update:Update, context:CallbackContext):
        print(f"Erhalten Nachricht von chat_id: {update.effective_chat.id}; text: {update.message.text}")

    def run(self):
        try:
            self.application = ApplicationBuilder().token(self.token).build()
            print("APP:",self.application)
            self.application.add_handler(CommandHandler('start', self.command_start))
            # self.application.add_handler(CommandHandler('send', self.test))
            self.application.add_handler(MessageHandler(filters.ALL, self.test))
            
            job_queue = self.application.job_queue
            print("job_queu", job_queue)
            if job_queue:
                job_queue.run_repeating(self.wait_mqtt_message, interval = 1)
            self.application.run_polling(allowed_updates = Update.ALL_TYPES)
        except error as e:
            print("ERROR: ", e)
            self.application = ApplicationBuilder().token(self.token).build()
            self.application.run_polling(allowed_updates = Update.ALL_TYPES)