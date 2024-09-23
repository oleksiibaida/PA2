import paho.mqtt.client as mqtt

host = "192.168.0.206"
port = 1883


topics = {"alarm", "pin"}

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with code {reason_code}")
    print("Subscribed to topics: ")
    for t in topics:
        client.subscribe(t)
        print("".join(t))


def on_message(client, userdata, msg):
    if(msg.topic == "alarm"):
        print("!!!ALARM: " + msg.payload.decode())
    elif(msg.topic == "pin"):
        print("PIN: " + msg.payload.decode())
    else:
        print("Recieved TOPIC: " + str(msg.topic) + " MES: " + msg.payload.decode())

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


client.on_connect = on_connect
client.on_message = on_message

client.connect(host, port, 60)
# client.publish(topic, "mes")
client.loop_forever()