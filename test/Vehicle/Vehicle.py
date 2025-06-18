import paho.mqtt.client as mqtt
import json
from web3 import Web3
import time
import os
import datetime

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

execution_step = 0
reservationsList = []

# Caminho dos Contratos:
CONTRACTS_DIR = 'build/contracts/'

# Carregando o "ABI" de Um Contrato Compilado:
def getContractData(contract_name: str):
    with open(f"{CONTRACTS_DIR}{contract_name}.abi", 'r') as abi_file:
        abi = json.loads(abi_file.read()) # Lendo Como Dicionário.
    return abi

contracts_addresses = {}

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
    client.publish("vehicle/contracts_addresses/server", str("OK"))

def showAccountsBalance():
    # Salvando os Endereços das Contas:
    ecocharge_account = w3.eth.accounts[int(os.environ.get('ECOCHARGE_ACCOUNT'))]
    eflux_account = w3.eth.accounts[int(os.environ.get('EFLUX_ACCOUNT'))]
    voltpoint_account = w3.eth.accounts[int(os.environ.get('VOLTPOINT_ACCOUNT'))]
    # Exibindo o Balanço dos Veículos:
    balance_wei = w3.eth.get_balance(w3.eth.accounts[1])
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Saldo da Conta do Veículo 1: {balance_wei} wei ({balance_eth} ETH)\n")
    balance_wei = w3.eth.get_balance(w3.eth.accounts[2])
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Saldo da Conta do Veículo 2: {balance_wei} wei ({balance_eth} ETH)\n")
    balance_wei = w3.eth.get_balance(w3.eth.accounts[3])
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Saldo da Conta do Veículo 3: {balance_wei} wei ({balance_eth} ETH)\n")
    # Exibindo o Balanço do Servidor "EcoCharge":
    balance_wei = w3.eth.get_balance(ecocharge_account)
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Saldo da Conta da Empresa 'EcoCharge': {balance_wei} wei ({balance_eth} ETH)\n")
    # Exibindo o Balanço do Servidor "E-FLux":
    balance_wei = w3.eth.get_balance(eflux_account)
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Saldo da Conta da Empresa 'E-Flux': {balance_wei} wei ({balance_eth} ETH)\n")
    # Exibindo o Balanço do Servidor "VoltPoint":
    balance_wei = w3.eth.get_balance(voltpoint_account)
    balance_eth = w3.from_wei(balance_wei, 'ether')
    print(f"Saldo da Conta da Empresa 'EcoCharge': {balance_wei} wei ({balance_eth} ETH)\n")

def mqttScheduleReservations(client, index):
    data = {
        "vehicleID": index,
        "actualBatteryPercentage": 100,
        "batteryCapacity": 51,
        "departureCityCodename": "v_conquista",
        "arrivalCityCodename": "fortaleza",
        "accountNumber": index
    }
    client.publish("vehicle/create_reservations/server", json.dumps(data))

def depositFunds(index):
    global reservationsList
    print(f"Depositando os Fundos das Reservas do Veículo '{index}':\n")
    vehicle_account = w3.eth.accounts[index]
    rl_contract = w3.eth.contract(address=contracts_addresses["ReservationLedger"], abi=getContractData("ReservationLedger")) # Reservas.
    escrow_contract = w3.eth.contract(address=contracts_addresses["Escrow"], abi=getContractData("Escrow")) # Escrow de Pagamento.
    assert Web3.is_address(vehicle_account), "Endereço da Conta do Veículo Inválido!\n"
    reservations = rl_contract.functions.getReservationsByCustomer(vehicle_account).call()
    # Convertendo a Tupla de Reservas para Dicionário:
    for res in reservations:
        res_dict = {
            "reservationID": res[0],
            "chargingStationID": res[1],
            "chargingPointID": res[2],
            "cityCodename": res[3],
            "companyName": res[4],
            "startTimestamp": datetime.datetime.fromtimestamp(res[5]).isoformat(),
            "finishTimestamp": datetime.datetime.fromtimestamp(res[6]).isoformat(),
            "price": res[7],
            "customer": res[8],
            "recipient": res[9],
            "status": res[10]
        }
        print(f"Informações da Reserva '{res_dict["reservationID"]}':\n")
        print(json.dumps(res_dict, indent=4)) # Printando a Reserva.
        reservationsList.append(res_dict)
    # Exibindo Mensagem de Sucesso:
    print(f"{len(reservationsList)} Reservas Recuperadas da Blockchain Para Memória de Trabalho.\n")
    for reservation in reservationsList:
        print(f"Depositando o Pagamento Para a Reserva '{reservation["reservationID"]}'!\n")
        tx_hash = escrow_contract.functions.depositFunds(reservation["reservationID"]).transact({
            'from': vehicle_account, # Endereço do Carro
            'value': reservation["price"], # Preço em "wei", Presente nas Informações da Reserva
            "nonce": w3.eth.get_transaction_count(vehicle_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 125000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)

def mqttStartCS(client):
    print(f"Iniciando as Sessões de Carregamento de Todas as Reservas:\n")
    for rs in reservationsList:
        data = {
            "reservationID": rs["reservationID"],
        }
        client.publish("vehicle/start_charging_session/server", json.dumps(data))

def mqttFinishCS(client):
    print(f"Finalizando as Sessões de Carregamento de Todas as Reservas:\n")
    for rs in reservationsList:
        data = {
            "reservationID": rs["reservationID"],
        }
        client.publish("vehicle/end_charging_session/server", json.dumps(data))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao Broker com Sucesso!\n")
        for topic in MQTT_TOPICS_SUBSCRIBER:
            client.subscribe(topic)
        mqttReceiveContractsAddresses(client)
    else:
        print(f"Falha na Conexão! Código de Retorno: {rc}\n")

def on_message(client, userdata, message):
    global contracts_addresses, execution_step
    decodedMessage = message.payload.decode()
    print("Mensagem MQTT Recebida:")
    print(f"{decodedMessage}\n")

    topic = message.topic.split("/")
    if len(topic) == 3:
        topic_action = topic[1]
    else:
        topic_action = "unknown"

    if topic_action == "contracts_addresses":
        # Exibindo o Balanço das Contas:
        showAccountsBalance()
        # Executando os Passos Seguintes:
        contracts_addresses = json.loads(decodedMessage)
        execution_step = 1  # Avançando Para o Próximo Passo.
        time.sleep(2)
        mqttScheduleReservations(client, 1)
        mqttScheduleReservations(client, 2)
        mqttScheduleReservations(client, 3)
        time.sleep(15)

    elif topic_action == "create_reservations" and execution_step == 1:
        time.sleep(2)
        depositFunds(1)
        depositFunds(2)
        depositFunds(3)
        execution_step = 2
        mqttStartCS(client)

    elif topic_action == "start_charging_session" and execution_step == 2:
        mqttFinishCS(client)
        execution_step = 3

    elif topic_action == "end_charging_session" and execution_step == 3:
        # Exibindo o Balanço das Contas:
        showAccountsBalance()
        print("Processo Finalizado com Sucesso!")

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
