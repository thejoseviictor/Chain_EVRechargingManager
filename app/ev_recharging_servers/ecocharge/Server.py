# Servidor da Empresa "EcoCharge", que Atua no Estado do Ceará -------------------------------------------------------------------------------------------------------

# Importando as Dependências:
import os # Para Usar Variáveis de Ambiente.
from flask import Flask, request, jsonify # Para Criar a API do Servidor e Seus End-Points.
from web3 import Web3 # Para Comunicação com a Blockchain Ganache.
import threading # Para Criar Múltiplas Instâncias.
from ReservationsManager import ReservationsManager # Que Manipula a Persistência de Dados das Reservas.
from ChargingStationsFile import ChargingStationsFile # Que Manipula a Persistência de Dados dos Postos de Recarga.
import ReservationHelper # Funções para Gerar Parâmetros para Reservas.
import mqttFunctions # Função para Configurar e Inicializar o MQTT.
from ContractUtils import connectGanacheWeb3, getContractsAddresses, getContractData
from ContractUtils import createReservationBlockchain, startChargingSession, markReservationAsPayed
from ContractUtils import markReservationsAsConfirmed, markReservationsAsCanceled

# Criando a Aplicação Flask:
app = Flask(__name__) # "__name__" se tornará "__main__" ao executar.

# Salvando o Nome da Empresa:
companyName = os.environ.get('COMPANY_NAME') # Variável de Ambiente do Docker Compose.

# Salvando o IP e Porta do Servidor Desta Empresa:
SERVER_IP = os.environ.get(f'{companyName.upper()}_SERVER_IP') # IP Definido no Docker-Compose.
SERVER_PORT = int(os.environ.get(f'{companyName.upper()}_SERVER_PORT')) # Porta Definida no Docker-Compose.

# Criando o Objeto dos Postos de Recarga no Banco de Dados:
chargingStationsData = ChargingStationsFile()

# Salvando as Informações do Ganache:
GANACHE_URL = os.environ.get('GANACHE_URL')
ECOCHARGE_ACCOUNT = int(os.environ.get('ECOCHARGE_ACCOUNT'))
EFLUX_ACCOUNT = int(os.environ.get('EFLUX_ACCOUNT'))
VOLTPOINT_ACCOUNT = int(os.environ.get('VOLTPOINT_ACCOUNT'))

# Conectando ao Ganache (Web3):
w3 = connectGanacheWeb3(GANACHE_URL)

# Configurando as Contas das Empresas no Ganache:
company_accounts = {
    "ecocharge": w3.eth.accounts[ECOCHARGE_ACCOUNT],
    "eflux": w3.eth.accounts[EFLUX_ACCOUNT],
    "voltpoint": w3.eth.accounts[VOLTPOINT_ACCOUNT]
}

# Recebendo os Endereços dos Contratos pelo "Owner":
contracts_addresses = getContractsAddresses()

# Formatando os Endereços Para Objetos de Contrato:
rl_contract = w3.eth.contract(address=contracts_addresses["ReservationLedger"], abi=getContractData("ReservationLedger"))
escrow_contract = w3.eth.contract(address=contracts_addresses["Escrow"], abi=getContractData("Escrow"))
csm_contract = w3.eth.contract(address=contracts_addresses["ChargingSessionManager"], abi=getContractData("ChargingSessionManager"))

# Criando o Objeto de Manipulação das Reservas:
reservationsManager = ReservationsManager(rl_contract)

# Rota Para Agendar as Reservas de um Veículo Específico:
@app.route('/reservation', methods=['POST'])
def createReservations():            
    # Tratando os Dados Recebidos:
    # Esperado: data = {"vehicleID": int, "batteryCapacity": float, "accountNumber": int, "reservationsRoute": list}
    data = request.json
    vehicleID = data.get('vehicleID') # ID do Veículo.
    batteryCapacity = data.get('batteryCapacity') # Capacidade de Bateria do Veículo em kWh.
    accountNumber = data.get('accountNumber') # Índice do Endereço da Carteira do Cliente na Blockchain.
    customerAddress = w3.eth.accounts[accountNumber] # Carteira do Cliente na Blockchain.
    reservationsRoute = data.get('reservationsRoute') # A Rota das Reservas.

    # Exibindo as Informações das Reservas Solicitadas:
    print(f"Dados do Veículo '{vehicleID}' Recebidos para Reservas em:\n")
    for city in reservationsRoute:
        print(f"Cidade: {city["name"]} | Empresa: {city["company"]}\n")

    # Verificando Se Existem Postos de Recarga Cadastrados Neste Servidor:
    if not chargingStationsData.chargingStationsList:
        print("Erro: Não Existem Postos de Recarga Cadastrados Neste Servidor!\n")
        return jsonify({"error": "Não Existem Postos de Recarga Cadastrados Neste Servidor!"}), 404  # Erro 404: Not Found - Recurso Não Encontrado.
    
    # Procurando os Postos de Recarga Que Atuam nas Cidades Solicitadas:
    lastReservationDuration = 0 # Um Incremento da Duração da Reserva Anterior no "Tempo para Alcançar" da Reserva Atual.
    for cs in chargingStationsData.chargingStationsList:
        for city in reservationsRoute:
            if cs["city_codename"] == city["codename"]:
                chargingStationID = cs["chargingStationID"] # Salvando o ID do Posto de Recarga.
                chargingPointID = ReservationHelper.chooseChargingPoint(chargingStationID, rl_contract) # Procurando um Ponto de Carregamento no Posto de Recarga.
                # Verificando Se Um Ponto de Carregamento Foi Encontrado:
                if not chargingPointID:
                    print("Erro: Não Existem Pontos de Carregamento Cadastrados Neste Servidor!\n")
                    return jsonify({"error": "Não Existem Pontos de Carregamento Cadastrados Neste Servidor!"}), 404  # Erro 404: Not Found - Recurso Não Encontrado.
                else:
                    city["timeToReach"] += lastReservationDuration # Somando a Duração da Reserva Anterior.
                    # Realizando uma Reserva na Cidade:
                    currentReservation = reservationsManager.createReservation(chargingStationID, chargingPointID, city["codename"], companyName,
                                                                               city["actualBatteryPercentage"], batteryCapacity, city["timeToReach"], customerAddress)
                    # Verificando Se a Reserva Foi Realizada:
                    if not currentReservation:
                        print(f"Não Foi Possível Realizar a Reserva em '{city["name"]}' Para o Veículo '{vehicleID}'\n")
                        return jsonify({"error": f"Não Foi Possível Realizar a Reserva em '{city["name"]}' Para o Veículo '{vehicleID}"}), 404 # Erro 404: Not Found
                    else:
                        # Enviando a Reserva Para Blockchain:
                        rs_status = createReservationBlockchain(w3, rl_contract, company_accounts[f"{companyName.lower()}"], vehicleID, currentReservation)
                        if not rs_status:
                            print(f"Não Foi Possível Realizar a Reserva em '{city["name"]}' Para o Veículo '{vehicleID}'\n")
                            return jsonify({"error": f"Não Foi Possível Realizar a Reserva em '{city["name"]}' Para o Veículo '{vehicleID}"}), 404 # Erro 404: Not Found
                        lastReservationDuration = currentReservation["duration"] # Salvando a Duração Desta Reserva.
    
    # Retorno de Sucesso:
    return f"Sucesso ao Realizas as Reservas do Veículo '{vehicleID}'", 200

# Rota Para Marcar as Reservas do Cliente Como Confirmadas e Fazer Escrow:
@app.route('/confirm_res', methods=['POST'])
def confirmReservations():
    # Tratando os Dados Recebidos:
    # Esperado: data = {"vehicleID": int, "customerAddress": hex}
    data = request.json # Recebendo os Dados em um Dicionário.
    vehicleID = data.get('vehicleID')
    customerAddress = data.get('customerAddress')
    # Solicitando as Confirmações e Escrows das Reservas na Blockchain:
    confirmed = markReservationsAsConfirmed(w3, rl_contract, escrow_contract, company_accounts[f"{companyName.lower()}"], customerAddress)
    if confirmed:
        return f"Sucesso ao Confirmar as Reservas do Veículo '{vehicleID}'", 200
    else:
        return jsonify({"error": "Erro Genérico!"}), 500

# Rota Para Marcar as Reservas do Cliente Como Canceladas:
@app.route('/cancel_res', methods=['POST'])
def cancelReservations():
    # Tratando os Dados Recebidos:
    # Esperado: data = {"vehicleID": int, "customerAddress": hex}
    data = request.json # Recebendo os Dados em um Dicionário.
    vehicleID = data.get('vehicleID')
    customerAddress = data.get('customerAddress')
    confirmed = markReservationsAsCanceled(w3, rl_contract, company_accounts[f"{companyName.lower()}"], customerAddress)
    if confirmed:
        return f"Sucesso ao Cancelar as Reservas do Veículo '{vehicleID}'", 200
    else:
        return jsonify({"error": "Erro Genérico!"}), 500

# Rota Para Iniciar uma Sessão de Carregamento:
@app.route('/start_cs', methods=['POST'])
def startCS():
    # Tratando os Dados Recebidos:
    # Esperado: data = {"reservationID": int}
    data = request.json # Recebendo os Dados em um Dicionário.
    reservationID = data.get('reservationID')
    # Solicitando a Inicialização da Sessão de Carregamento na Blockchain:
    started = startChargingSession(w3, csm_contract, company_accounts[f"{companyName.lower()}"], reservationID)
    # Solicitando a Atualização do Status da Reserva Para "PAYED":
    rs_status = markReservationAsPayed(w3, rl_contract, company_accounts[f"{companyName.lower()}"], reservationID)
    if started and rs_status:
        return f"Sucesso ao Iniciar a Sessão de Carregamento da Reserva '{reservationID}'", 200
    else:
        return jsonify({"error": "Erro Genérico!"}), 500

# Rodando o Servidor no IP da Máquina:
if __name__ == '__main__':
    # Iniciando o MQTT em Outra Thread:
    mqtt_thread = threading.Thread(target=mqttFunctions.startMQTT) # Configurando a Thread do MQTT.
    mqtt_thread.daemon = True # Thread "Daemon" Que Se Encerrará Junto Com o Servidor.
    mqtt_thread.start() # Iniciando a Thread do MQTT.

    # Iniciando o Servidor HTTP (Flask):
    app.run(host=SERVER_IP, port=SERVER_PORT, debug=True, use_reloader=False)
