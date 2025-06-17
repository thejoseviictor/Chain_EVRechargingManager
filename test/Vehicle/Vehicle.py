import paho.mqtt.client as mqtt
import json
from web3 import Web3
import time
import os

GANACHE_URL = os.environ.get('GANACHE_URL')
BROKER_IP = os.environ.get('MQTT_BROKER_HOST')
BROKER_PORT = os.environ.get('MQTT_BROKER_PORT')
MQTT_TOPICS_PUBLISHER = {
    "vehicle/contracts_addresses/server",
    "vehicle/create_reservations/server",
    "vehicle/start_charging_session/server",
    "vehicle/end_charging_session/server"
}
MQTT_TOPICS_SUBSCRIBER = {
    "server/contracts_addresses/vehicle",
    "server/create_reservations/vehicle",
    "server/start_charging_session/vehicle",
    "server/end_charging_session/vehicle"
}

while True:
    try:
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        if not w3.is_connected():
            raise Exception("Não foi Possível Conectar-se Ao Ganache!\n")
        print("Conectado ao Ganache!")
        break
    except Exception as e:
        print(f"Erro de Conexão ao Ganache: {e}\n")
        time.sleep(3) # Tempo de Espera Para Tentar uma Nova Conexão.

def mqttReceiveContractsAddresses(client):
    client.publish("vehicle/contracts_addresses/server", "OK")

def mqttScheduleReservations(client):
    data = {
        "vehicleID": 1,
        "actualBatteryPercentage": 100,
        "batteryCapacity": 51,
        "departureCityCodename": "v_conquista",
        "arrivalCityCodename": "e_cunha",
        "accountNumber": 1
    }
    client.publish("vehicle/create_reservations/server", json.dumps(data))

def depositFunds():
    pass

def mqttStartCS(client):
    data = {
        "reservationID": 1,
    }
    client.publish("vehicle/start_charging_session/server", json.dumps(data))

def mqttFinishCS(client):
    data = {
        "reservationID": 1,
    }
    client.publish("vehicle/end_charging_session/server", json.dumps(data))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao Broker com Sucesso!\n")
        for topic in MQTT_TOPICS_SUBSCRIBER:
            client.subscribe(topic)
        mqttReceiveContractsAddresses(client)
        mqttScheduleReservations(client)
        depositFunds()
        mqttStartCS(client)
        mqttFinishCS(client)
    else:
        print(f"Falha na Conexão! Código de Retorno: {rc}\n")

def on_message(client, userdata, msg):
    print(f"[Recebido] Tópico: {msg.topic} | Mensagem: {msg.payload.decode()}\n")

def on_publish(client, userdata, mid):
    print("Mensagem Publicada Com Sucesso!\n")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

client.reconnect_delay_set(min_delay=3,max_delay=30)
client.connect_async(BROKER_IP, int(BROKER_PORT), 60)

client.loop_start()

try:
    while True:
        pass 
except KeyboardInterrupt:
    print("Encerrando...")
    client.loop_stop()
    client.disconnect()
