# Servidor da Empresa "EcoCharge", que Atua no Estado do Ceará -------------------------------------------------------------------------------------------------------

# Importando as Dependências:
import os # Para Usar Variáveis de Ambiente.
from flask import Flask, request, jsonify # Para Criar a API do Servidor e Seus End-Points.
from web3 import Web3 # Para Comunicação com a Blockchain Ganache.
import threading # Para Criar Múltiplas Instâncias.
from ReservationsFile import ReservationsFile # Que Manipula a Persistência de Dados das Reservas.
from ChargingStationsFile import ChargingStationsFile # Que Manipula a Persistência de Dados dos Postos de Recarga.
import ReservationHelper # Funções para Gerar Parâmetros para Reservas.
import mqttFunctions # Função para Configurar e Inicializar o MQTT.
from Utils import sendReservationsToOtherServers, connectGanacheWeb3 # Função Para Enviar Solicitações de Reservas Para Outros Servidores.

# Salvando o Nome da Empresa:
companyName = os.environ.get('COMPANY_NAME') # Variável de Ambiente do Docker Compose.

# Salvando o IP e Porta do Servidor Desta Empresa:
SERVER_IP = os.environ.get(f'{companyName.upper()}_SERVER_IP') # IP Definido no Docker-Compose.
SERVER_PORT = int(os.environ.get(f'{companyName.upper()}_SERVER_PORT')) # Porta Definida no Docker-Compose.

# Criando o Objeto das Reservas no Banco de Dados:
reservationsData = ReservationsFile()

# Criando o Objeto dos Postos de Recarga no Banco de Dados:
chargingStationsData = ChargingStationsFile()

# Criando a Aplicação Flask:
app = Flask(__name__) # "__name__" se tornará "__main__" ao executar.

# Salvando as Informações do Ganache:
GANACHE_URL = os.environ.get('GANACHE_URL')
ECOCHARGE_ACCOUNT = int(os.environ.get('ECOCHARGE_ACCOUNT'))
EFLUX_ACCOUNT = int(os.environ.get('EFLUX_ACCOUNT'))
VOLTPOINT_ACCOUNT = int(os.environ.get('VOLTPOINT_ACCOUNT'))

# Conectando ao Ganache e Web3:
w3 = connectGanacheWeb3(GANACHE_URL)

# Configurando as Contas do Ganache:
accounts = w3.eth.accounts
ecocharge_account = accounts[ECOCHARGE_ACCOUNT]
eflux_account = accounts[EFLUX_ACCOUNT]
voltpoint_account = accounts[VOLTPOINT_ACCOUNT]

# Rota Para Agendar as Reservas de um Veículo Específico, de Acordo com a Lista da Rota de Reservas (Servidor-Servidor):
@app.route('/reservation', methods=['POST'])
def createReservations():
    pass

# Rodando o Servidor no IP da Máquina:
if __name__ == '__main__':
    # Iniciando o MQTT em Outra Thread:
    mqtt_thread = threading.Thread(target=mqttFunctions.startMQTT) # Configurando a Thread do MQTT.
    mqtt_thread.daemon = True # Thread "Daemon" Que Se Encerrará Junto Com o Servidor.
    mqtt_thread.start() # Iniciando a Thread do MQTT.

    # Iniciando o Servidor HTTP (Flask):
    app.run(host=SERVER_IP, port=SERVER_PORT, debug=True, threaded=True) # Threaded = O Flask Pode Tratar Múltiplas Requisições Ao Mesmo Tempo.
