from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup, error
from telegram.ext import Updater, filters, ConversationHandler, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackContext
import threading
import json
import db
from queue import Queue, Empty
import cv2
from pyzbar.pyzbar import decode
import os
import aiohttp

#Definiere States fuer die Kommunikation
SEND_DEVICE_ID, HOME_PAGE = range(2)

class Bot(threading.Thread):
    def __init__(self,queue,token):
        threading.Thread.__init__(self)
        self.token = token
        self.queue = queue
        self.db_json = 'include/users.json'
        self.messages = self.load_messages_json()
        # Verbidnung zum DB
        self.db = db.Datenbank()

    def load_messages_json(self):
        with open("include/messages.json", 'r', encoding='utf-8') as file:
            return json.load(file)

    
    def get_db_json(self):
        try:
            with open(self.db_json, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
        
    async def send_many_messages(self, users: list, msg_type: str = None, text: str = None):
        """
        Sendet gleiche Nachricht an alle IDs in users
        :param users: List von users
        """
        if len(users) == 0:
            print("TG-BOT: Kein User uebergeben")
            return
        for user in users:
            await self.send_message(user=user, msg_type=msg_type, text=text)

    async def send_message(self, user: dict, msg_type: str = None, text: str = None):
        """
        Sendet eine Nachricht in Telegram-Bot
        :param self:
        :param user: User, der die Nachricht erhaelt
        :param msg_type: OPTIONAL Name des Nachricht in messages.json
        :param text: OPTIONAL freier Text
        Einer der beiden Parameters muss ueberegen sein
        """
    
        msg_text = ""
        if msg_type is not None:
            language = user['language_code'] if user['language_code'] in self.messages else "en"
            msg_text = self.messages[msg_type][language].format(username = user['username'] if user['username'] else user['first_name'])
        elif text is not None:
            msg_text = text
        else:
            print("TG-BOT: Kein Text fuer die Nachricht uebergeben")
            return
        
        print('TG-BOT: Nachricht senden: CHAT:', user['id'], "Text:", msg_text)
        await self.application.bot.send_message(user['id'], msg_text)

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
        topic, dev_id = mqtt_message['topic'].split('/')
        print("topic", topic, "dev_id", dev_id)
        users = self.db.get_users_on_device(dev_id)
        mqtt_text = mqtt_message['text']
        msg_text = ""
        if topic == "alarm":
            if mqtt_text == 'fire_start':
                await self.send_many_messages(users=users, msg_type="fire_start")
            elif mqtt_text == 'fire_stop':
                await self.send_many_messages(users=users, msg_type="fire_stop")
        elif topic == "status":
            print("topic status")
        else:
            print("unknown topic")    
        """ BACKUP
        if mqtt_message['topic'] == "alarm":
            if mqtt_message['text'] == 'fire_start':
                msg_text = "🔥ALARM🔥\nFEUER\n"
                await self.send_message()
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
                await self.send_message('status feuer')"""

    async def test(self, update:Update, context:CallbackContext):
        print("TEST")
        mqtt_message = {"topic": "alarm/123", "text": "fire_start"}
        await self.handle_mqtt_message(mqtt_message)

    async def fallback(self, update:Update, context:CallbackContext):
        msg_text = self.messages["cancel_conversation"][update.effective_user.language_code]
        await self.application.bot.send_message(update.effective_user.id, msg_text)

    async def command_start(self, update:Update, context:CallbackContext):
        user = update.effective_user.to_dict()
        if self.db.user_exists(user['id']):
            print("user exists")
            return HOME_PAGE
        else:
            print("new user")
            await self.send_message(user, "new_user_welcome_message")
            return SEND_DEVICE_ID

    async def get_device_id(self, update:Update, context:CallbackContext):
        print("GET DEVICE ID")
        user = update.effective_user.to_dict()
        dev_id = update.effective_message.text
        print('dev_id:', dev_id)
        if self.check_device_id(dev_id):
            self.db.add_user(user_data=user, device_id=dev_id)
            await self.send_message(user=user, msg_type="welcome_message")
            return HOME_PAGE
        else:
            await self.send_message(user=user, msg_type="wrong_device_id")
            return SEND_DEVICE_ID


    async def get_device_id_qr(self, update:Update, context:CallbackContext):
        # GET Daten aus der geschickte Datei oder Photo
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
        elif update.message.document and update.message.document.mime_type.startswith("image/"):
            file = await update.message.document.get_file()
        else:
            self.send_message(user=update.effective_user, msg_type="qr_code_wrong_format")

        # Pfad zur Datei definieren
        path = fr"include\qr_codes\qr_code_{update.effective_chat.id}.jpg"
        # Datei herunterladen
        try:
            file_url = file.file_path
            print("file_url:", file_url)
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        with open(path, 'wb') as _:
                            _.write(await response.read())
                    else:
                        self.send_message(user=update.effective_user.to_dict(), msg_type="file_download_error")
                        return SEND_DEVICE_ID
        except Exception as e:
            print("FILE_DOWNLOAD_EXEPTION:",e)
            await self.send_message(user=update.effective_user.to_dict(), msg_type="qr_code_wrong_format")
            return SEND_DEVICE_ID
        
        try:
            file = cv2.imread(path)
            file = decode(file)

            if file:
                for _ in file:
                    qr_text = _.data.decode('utf-8')
                    print("device_id QR:", qr_text)
                    if self.check_device_id(qr_text):
                        self.db.add_user(user_data=update.effective_user.to_dict(), device_id=qr_text)
                        await self.send_message(user=update.effective_user.to_dict(), msg_type="welcome_message")
                        return HOME_PAGE
                    else:
                        await self.send_message(user=update.effective_user.to_dict(), msg_type="no_qr_code_photo")
                        return SEND_DEVICE_ID
            else:
                await self.send_message(user=update.effective_user, msg_type="no_qr_code")
                return SEND_DEVICE_ID
        except Exception as e:
            print("FILE_ERROR:",e)
        finally:
            if os.path.exists(path):
                os.remove(path)


        
    async def command_home(self, update:Update, context:CallbackContext):
        user = update.effective_user.to_dict()
        await self.send_message(user=user, text="Welcome on Home Page")
    

        

    def check_device_id(self, id: str):
        """TODO CHekc if device has license"""
        if len(id) > 10 or type(id) != str:  return 0
        return 1

    def init_handlers(self):
        test_handler = CommandHandler('test', self.test)
        start_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.command_start)],
            states={
                SEND_DEVICE_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_device_id),
                    MessageHandler(filters.PHOTO | filters.Document.IMAGE, self.get_device_id_qr)
                ],
                HOME_PAGE: [
                    CommandHandler('home', self.command_home)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.fallback)]
        )
        self.application.add_handlers([test_handler,start_handler])
        print("HANDLERS INIT")

    def run(self):
        try:
            self.application = ApplicationBuilder().token(self.token).build()
            # self.application.add_handler(MessageHandler(filters.ALL, self.test))
            self.init_handlers()
            job_queue = self.application.job_queue
            if job_queue:
                job_queue.run_repeating(self.wait_mqtt_message, interval = 1)
            self.application.run_polling(allowed_updates = Update.ALL_TYPES)
        except error as e:
            print("ERROR: ", e)
            self.application = ApplicationBuilder().token(self.token).build()
            self.application.run_polling(allowed_updates = Update.ALL_TYPES)