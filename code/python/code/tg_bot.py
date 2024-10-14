from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Updater, filters, ConversationHandler, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackContext
import threading
from queue import Queue, Empty
class Bot(threading.Thread):
    def __init__(self,queue,token):
        threading.Thread.__init__(self)
        self.token = token
        self.queue = queue

    async def command_start(self, update:Update, context:CallbackContext):
        self.chat_id = update.effective_chat.id
        print('Chatid: ',self.chat_id)
        print('Fullname: ', update.effective_chat.full_name)
        print('USername: ',update.effective_user.name)
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
            if mqtt_message['text'] == 'feuer':
                await self.send_message("🔥ALARM🔥\nFEUER\n")
            elif mqtt_message['text'] == 'gas':
                await self.send_message("💨ALARM💨\nGAS\n")
            elif mqtt_message['text'] == 'pir':
                await self.send_message("🥷ALARM🥷\nFremdbewegung Erkannt\nAlarm einschalten?")
                #TODO Turn on Alarm
            elif mqtt_message['text'] == 'wrongpin':
                await self.send_message("🔒ALARM🔒\nFalsche PIN wurde eingegeben!\n Alarm einschalten?")
        elif mqtt_message['topic'] == "status":
            if mqtt_message['text'] == 'pinchanged':
                await self.send_message("Neue PIN eingegeben")
            elif mqtt_message['text'] == 'feuer':
                await self.send_message('status feuer')

    async def test(self, update:Update, context:CallbackContext):
        print(f"Erhalten Nachricht von chat_id: {update.effective_chat.id}; text: {update.message.text}")

    def run(self):
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