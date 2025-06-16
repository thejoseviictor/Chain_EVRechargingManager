# Funções do MQTT do Servidor -----------------------------------------------------------------------------------------------------------------------------------------------------

# Importando as Dependências:
import os # Para Usar Variáveis de Ambiente.
import json # Para Printar os Erros.
import requests # Para Comunicação com Outros Servidores.
import paho.mqtt.client as mqtt # Funções do MQTT.
from Server import SERVER_IP, SERVER_PORT, contracts_addresses
from ContractUtils import OWNER_IP, OWNER_PORT
import ReservationHelper # Funções para Gerar Parâmetros para Reservas.

# Salvando as Informações do MQTT:
MQTT_BROKER_HOST = os.environ.get('MQTT_BROKER_HOST') # Variável de Ambiente do Docker Compose.
MQTT_BROKER_PORT = os.environ.get('MQTT_BROKER_PORT') # Variável de Ambiente do Docker Compose.
# Salvando os Tópicos "Subscriber" e "Publisher":
# Formato Reconhecido = "from/action/to"
MQTT_TOPICS_SUBSCRIBER = {
    "vehicle/contracts_addresses/server",
    "vehicle/create_reservations/server",
    "vehicle/start_charging_session/server",
    "vehicle/end_charging_session/server"
}
MQTT_TOPICS_PUBLISHER = {
    "server/contracts_addresses/vehicle",
    "server/create_reservations/vehicle",
    "server/start_charging_session/vehicle",
    "server/end_charging_session/vehicle"
}

# Verificando a Existência de Json:
def isJson(text):
    try:
        json_object = json.loads(text)
        return True
    except ValueError:
        return False

# Descobrindo em Qual Tópico Publicar no MQTT:
def findPublisherTopic(action: str, destination: str):
    for topic in MQTT_TOPICS_PUBLISHER:
        topicParts = topic.split("/")
        if len(topicParts) == 3:
            if topicParts[1] == action and topicParts[2] == destination:
                return topic
    return None

# Função Para Enviar os Endereços dos Contratos do Ganache:
def mqttSendContractsAddresses(client, action: str):
    publisherTopic = findPublisherTopic(action, "vehicle")
    if publisherTopic:
        client.publish(publisherTopic, json.dumps(contracts_addresses))
        print("Endereços dos Contratos Ganache Enviados Atráves do MQTT\n")

# Função para Criar Reservas, Recebida por um Tópico do MQTT:
def mqttCreateReservations(client, action: str, vehicleData: dict):
    # Descobrindo em Qual Tópico Publicar:
    publisherTopic = findPublisherTopic(action, "vehicle")
    if not publisherTopic:
        return # Caso o Tópico de Publicação Não Seja Encontrado.

    # Separando as Informações do Parâmetro em Variáveis:
    vehicleID = vehicleData["vehicleID"] # ID do Veículo.
    actualBatteryPercentage = vehicleData["actualBatteryPercentage"] # Porcentagem Atual de Bateria do Veículo.
    batteryCapacity = vehicleData["batteryCapacity"] # Capacidade de Bateria do Veículo em kWh.
    departureCityCodename = vehicleData["departureCityCodename"] # Apelido da Cidade de Partida.
    arrivalCityCodename = vehicleData["arrivalCityCodename"] # Apelido da Cidade de Destino.
    accountNumber = int(vehicleData["accountNumber"]) # Índice do Endereço da Carteira do Cliente na Blockchain.

    # Descobrindo a Rota da Cidade de Partida para a Cidade de Destino:
    reservationsRoute = ReservationHelper.chooseChargingStations(vehicleID, departureCityCodename, arrivalCityCodename, actualBatteryPercentage, batteryCapacity)

    # Caso Não Encontre Uma Rota:
    if not reservationsRoute:
        client.publish(publisherTopic, str({"error": vehicleID}))
        print("Erro ao Encontrar Uma Rota Para os Agendamentos\n")
        return

    # Estrutura Com Parâmetros Para Reserva:
    data = {
        "vehicleID": vehicleID,
        "batteryCapacity": batteryCapacity,
        "accountNumber": accountNumber,
        "reservationsRoute": reservationsRoute
    }

    # Separando as Reservas de Cada Servidor:
    ecoChargeReservationsRoute = [r for r in reservationsRoute if r.get("company") == "ecocharge"]
    eFluxReservationsRoute = [r for r in reservationsRoute if r.get("company") == "eflux"]
    voltPointReservationsRoute = [r for r in reservationsRoute if r.get("company") == "voltpoint"]

    # Endereços dos Servidores das Empresas:
    ECOCHARGE_RESERVATION_ADDRESS = f'http://{os.environ.get('ECOCHARGE_SERVER_IP')}:{int(os.environ.get('ECOCHARGE_SERVER_PORT'))}/reservation'
    EFLUX_RESERVATION_ADDRESS = f'http://{os.environ.get('EFLUX_SERVER_IP')}:{int(os.environ.get('EFLUX_SERVER_PORT'))}/reservation'
    VOLTPOINT_RESERVATION_ADDRESS = f'http://{os.environ.get('VOLTPOINT_SERVER_IP')}:{int(os.environ.get('VOLTPOINT_SERVER_PORT'))}/reservation'

    # Verificando as Respostas e Tomando Decisôes:
    success = True
    try:
        # Adicionando a Tarefa APENAS Se Houver Rota Para o Servidor:
        tasks = []
        if ecoChargeReservationsRoute:
            data["reservationsRoute"] = ecoChargeReservationsRoute
            tasks.append(requests.post(ECOCHARGE_RESERVATION_ADDRESS, json=data, timeout=5))
        if eFluxReservationsRoute:
            data["reservationsRoute"] = eFluxReservationsRoute
            tasks.append(requests.post(EFLUX_RESERVATION_ADDRESS, json=data, timeout=5))
        if voltPointReservationsRoute:
            data["reservationsRoute"] = voltPointReservationsRoute
            tasks.append(requests.post(VOLTPOINT_RESERVATION_ADDRESS, json=data, timeout=5))
        # Analisando as Respostas dos Servidores:
        for response_task in tasks:
            if not response_task.ok:
                success = False
                break
        # Verificando Se Todas as Respostas Foram de Sucesso:
        if success:
            client.publish(publisherTopic, str({"success": vehicleID}))
            response = requests.post(f'http://{SERVER_IP}:{SERVER_PORT}/confirm_res', json=json, timeout=5)
            print(f"Todas as Reservas Para o Veículo '{vehicleID}' Foram Agendadas Com Sucesso!\n")
        else:
            client.publish(publisherTopic, str({"error": vehicleID}))
            response = requests.post(f'http://{SERVER_IP}:{SERVER_PORT}/cancel_res', json=json, timeout=5)
            print(f"Alguns Servidores Retornaram Erro nas Reservas Para o Veículo '{vehicleID}'.")
    # Tratando as Exceções, Se o Servidor Não Responder:
    except Exception as e:
        client.publish(publisherTopic, str({"error": vehicleID}))
        print(f"Erro no Agendamento das Reservas: {e}\n")

# Função Para Inicializar Uma Sessão de Carregamento:
def mqttStartCS(client, action: str, json: dict):
    publisherTopic = findPublisherTopic(action, "vehicle")
    if publisherTopic:
        # Solicitando a Inicialização da Sessão de Carregamento Através da API Local:
        try:
            response = requests.post(f'http://{SERVER_IP}:{SERVER_PORT}/start_cs', json=json, timeout=5)
            if response.ok:
                client.publish(publisherTopic, str({"success": json["reservationID"]}))
                print(f"{response.text}\n") # Exibindo a Resposta de Sucesso.
            else:
                try:
                    errorMessage = response.json().get("error")
                except ValueError:
                    errorMessage = "Erro Desconhecido"
                client.publish(publisherTopic, str({"error": json["reservationID"]}))
                print(f"Erro na Inicialização da Sessão de Carregamento ({response.status_code}): {errorMessage}\n")
        # Tratando as Exceções, Se o Servidor Não Responder:
        except Exception as e:
            client.publish(publisherTopic, str({"error": json["reservationID"]}))
            print(f"Erro na Inicialização da Sessão de Carregamento: {e}\n")

# Função Para Finalizar Uma Sessão de Carregamento:
def mqttFinishCS(client, action: str, json: dict):
    publisherTopic = findPublisherTopic(action, "vehicle")
    if publisherTopic:
        # Solicitando a Finalização da Sessão de Carregamento Através da API do "Owner" da Blockchain:
        try:
            response = requests.post(f'http://{OWNER_IP}:{OWNER_PORT}/finish_cs', json=json, timeout=5)
            if response.ok:
                client.publish(publisherTopic, str({"success": json["reservationID"]}))
                print(f"{response.text}\n") # Exibindo a Resposta de Sucesso.
            else:
                try:
                    errorMessage = response.json().get("error")
                except ValueError:
                    errorMessage = "Erro Desconhecido"
                client.publish(publisherTopic, str({"error": json["reservationID"]}))
                print(f"Erro na Finalização da Sessão de Carregamento ({response.status_code}): {errorMessage}\n")
        # Tratando as Exceções, Se o Servidor Não Responder:
        except Exception as e:
            client.publish(publisherTopic, str({"error": json["reservationID"]}))
            print(f"Erro na Finalização da Sessão de Carregamento: {e}\n")

# Função "callback" ao Conectar-se ao Broker MQTT:
def onConnect(client, userdata, flags, rc): # Assinatura Padrão da Função.
    if rc == 0:
        print("Conectado ao Broker Com Sucesso!\n")
        # Increvendo o Servidor nos Tópicos do MQTT:
        for topic in MQTT_TOPICS_SUBSCRIBER:
            client.subscribe(topic)
    else:
        print(f"Falha na Conexão Com o Broker! Código de Retorno: {rc}\n")

# Função "callback" ao Perder Conexão Com o Broker MQTT:
def onDisconnect(client, userdata, rc):
    if rc != 0:
        print("Conexão Com o Broker Perdida! Tentando Reconectar...\n")

# Função "callback" ao Receber uma Mensagem do MQTT:
def onMessage(client, userdata, message): # Assinatura Padrão da Função.
    # Manipulando a Mensagem:
    decodedMessage = message.payload.decode() # Decodificando a Mensagem, Convertendo Bytes em String.
    print("Mensagem MQTT Recebida:")
    print(f"{decodedMessage}\n")

    # Verificando a Existência de Json:
    if isJson(decodedMessage):
        jsonMessage = json.loads(decodedMessage) # Transformando a Mensagem em Dicionário.
        print(json.dumps(jsonMessage, indent=4)) # Mensagem Identada.
        print("\n")

    # Salvando o Tópico e Separando a Ação:
    topic = message.topic.split("/") # Salvando as Partes do Tópico em uma Lista: ["from", "action", "to"]
    if len(topic) == 3: # Formato de Tópico Conhecido: ["from", "action", "to"]
        topic_action = topic[1] # Salvando a Ação do Tópico.
    else:
        topic_action = "unknown" # Formato de Tópico Desconhecido.
    
    # Tópico para Enviar os Endereços dos Contratos do Ganache:
    if topic_action == "contracts_addresses":
        mqttSendContractsAddresses(client, topic_action)
    
    # Tópico de Criação de Reservas:
    elif topic_action == "create_reservations":
        expectedKeys = ["vehicleID", "actualBatteryPercentage", "batteryCapacity", "departureCityCodename", "arrivalCityCodename", "accountNumber"] # Chaves Esperadas na Mensagem.
        if all(key in jsonMessage for key in expectedKeys): # Verificando Se Todas as Chaves Estão Presentes.
            mqttCreateReservations(client, topic_action, jsonMessage) # Passando as Informações do Veículo Para a Função.
        else:
            missingKeys = [key for key in expectedKeys if key not in jsonMessage]
            print(f"Agendamento das Reservas Impedido, Pois Não Foram Enviadas as Seguintes Informações: {missingKeys}\n")
    
    # Tópico Para Iniciar uma Sessão de Carregamento:
    # Esperado: {"reservationID", value}
    elif topic_action == "start_charging_session":
        if "reservationID" in jsonMessage:
            mqttStartCS(client, topic_action, jsonMessage)
        else:
            print(f"Inicialização da Sessão de Carregamento Impedida, Pois o ID da Reserva Não Foi Indicado!\n")
    
    # Tópico Para Finalizar uma Sessão de Carregamento:
    # Esperado: {"reservationID", value}
    elif topic_action == "end_charging_session":
        if "reservationID" in jsonMessage:
            mqttFinishCS(client, topic_action, jsonMessage)
        else:
            print(f"Finalização da Sessão de Carregamento Impedida, Pois o ID da Reserva Não Foi Indicado!\n")
    
    # Ação Desconhecida no Tópico:
    else:
        print(f"Ação Desconhecida no Tópico: {message.topic}\n")

# Função "callback" ao Publicar uma Mensagem no MQTT:
def onPublish(client, userdata, mid):
    print("Mensagem Publicada Com Sucesso!\n")

# Configurando e Iniciando o MQTT:
def startMQTT():
    client = mqtt.Client() # Salvando o Cliente MQTT.
    client.on_connect = onConnect # Salvando a Função de "callback", Que Será Passada Como Parâmetro ao Conectar-se ao Broker.
    client.on_disconnect = onDisconnect # Salvando a Função de "callback", Que Será Passada Como Parâmetro ao Perder Conexão Com o Broker.
    client.on_message = onMessage # Salvando a Função de "callback", Que Será Passada Como Parâmetro ao Receber uma Mensagem.
    client.on_publish = onPublish # Salvando a Função de "callback", Que Será Passada Como Parâmetro ao Publicar uma Mensagem.
    # Configurações de Conexão Com o Broker:
    client.reconnect_delay_set(min_delay=3,max_delay=30) # Tempo de Reconexão.
    client.connect_async(MQTT_BROKER_HOST, int(MQTT_BROKER_PORT), 60) # Conexão Assíncrona Com o Broker, Com "Keep Alive" (Avisos) de 60 Segundos.
    client.loop_start() # Iniciando o Loop de Recebimento das Mensagens.
