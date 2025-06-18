'''
Grupo: João Macedo, José Vitor

Componente Curricular: TEC502 - MI - Concorrência e conectividade 

Concluido em: 21/04/2025;

Declaro que este código foi elaborado por mim e pelo meu grupo de forma individualmente 
e não contém nenhum trecho de código de outro colega ou de outro autor, tais como provindos 
de livros e  apostilas, e páginas ou documentos eletrônicos da Internet. Qualquer trecho de 
código de outra autoria que não a minha está destacado com uma citação para o autor e a fonte 
do código, e estou ciente que estes trechos não serão considerados para fins de avaliação.

'''

''' Classe main do veiculo'''

#--------------------------------------------------------------------------------------------------------------

from faker import Faker # Biblioteca utilizada para a geração de dados fictícios

import time # Biblioteca usada para fluxos e simulações de tempo
import random # Biblioteca usada para gerar dados e valores aleatórios
import re  # Biblioteca que permite buscas, substituições e manipulação em str

import sys # Bibliotecas usadas para trabalhar com caminhos, fluxo entre diretórios e entradas 
import os  # e saidas diretamente com o sistema/terminal
from pathlib import Path
import paho.mqtt.client as mqtt
import json # Biblioteca usada para trabalhar com arquivos .json e importar dados fictícios para o sistema

from web3 import Web3 # Biblioteca para comunicação e controle com o Ganache

#--------------------------------------------------------------------------------------------------------------

# Importação de classes base para o funcionamnto do sistema:

from Vehicle import Vehicle
from VehicleUtility import VehicleUtility
from User import User
from VehicleClient import VehicleClient

#--------------------------------------------------------------------------------------------------------------

# Variaveis usadas para fluxo entre caminhos e diretórios de pastas e arquivos de persistência de dados

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))) # Adiciona dinamicamente o diretório absoluto em sys.path

BASE_DIR = Path(__file__).resolve().parent # Caminho do script "main.py"
DATA_PATH = BASE_DIR / 'dataPath' # Caminho da pasta "dataPath"

#Definindo o caminho de cada arquivo de dados
dataFilePath = str(DATA_PATH / 'data.json')
reservationsFilePath = str(DATA_PATH / 'reservations.json')
reservation_ledger_abiFilePath = str(DATA_PATH / 'reservation_ledger_abi.json')
escrow_abi_FilePath = str(DATA_PATH / 'escrow_abi.json')

# Métodos utilitários --------------------------------------------------------------------------

''' Classe de utilidades, nela há a chamada para processos de comunicação,
    processos de exibição amigável ao úsuario e entre outro processos
'''
utility = VehicleUtility() 

#------------------------------------------------------------------------------------------------

ganache_URL = os.environ.get("GANACHE_URL")

an = os.environ.get("ACCOUNT_NUMBER")

account_number = 0

if an:
    account_number = int(an) # Número da conta Ganache utilizada pelo respectivo veículo(0-9). Deve ser alterado no docker-compose para cada conta nova de veículo.

repeat = True # Variavel usada para lidar com o fluxo de repetição do programa.
firstLogin = True # Variavel para indicar que apenas um login é preciso por execução.

account_address = '' # Variavel para determinar o endereço de conta Ganache
contracts_addresses = {} # Variavel para receber o endereço de contrato do servidor

type_subscribe = 0 # Variavel para definir o tipo de publish/subscribe na classe de comunicação 'VehicleClient'

ID_reservation = ''

''' 
    ^ Os valores e suas respectivas descrições são :

    1 - Para receber todos os endereços de contrato (AuthorizedServers.sol, ChargingSession.sol, Escrow.sol e ReservationLedger.sol)
    2 - Para solicitar reserva e receber os IDs correspondentes
    3 - Para iniciar uma recarga
    4 - Para finalizar uma recarga

'''
route = ['','']

#------------------------------------------------------------------------------------------------

# Definição de conta e dados fictícios

fake = Faker("pt_BR") # Biblioteca usada para gerar dados aleatórios para usuário e veiculo
            
# User ----------------------------------------------------------------------------------------------------------------

cpf = re.sub(r'\D', '', fake.cpf())
            
fakeName = []
fakeName.append(fake.first_name())
fakeName.append(fake.last_name())

# Processo de normalização do nome gerado por faker, evitando assim formatações indesejadas de str por conta de acentos e cê-cedilha 
genericName = utility.nomalizeName(fakeName)

firstName = genericName[0]
lastName = genericName[1]

name = firstName + " " + lastName

# Lista e variavel para determinar um domínio aleatório para o email
genericDomain = ["@gmail.com", "@outlook.com", "@hotmail.com", "@yahoo.com", "@bol.com"]
randomDomain = random.randint(0,4)

email = re.sub(r"\s+", "", firstName.lower() + "." + lastName.lower() + genericDomain[randomDomain])

# Senha aleatória 
password = fake.password(length=8, special_chars=True, digits=True, upper_case=True, lower_case=True)
# Parâmetros: Tamanho(8), caracteres especiais(s), números(s), letras maiusculas(s), letras minusculas(s)

user = User(cpf = cpf, name = name, email = email , password = password)

# Vehicle -------------------------------------------------------------------------------------------------------------

genericID = random.randint(1,99999) # Gera um ID aleatório de 5 dígitos para o veículo
vid = str(genericID).zfill(5)

owner = user 
licensePlate = fake.license_plate()
moneyCredit = round(10000, 2) # O valor de crédito do veiculo inicia com R$10.000
currentEnergy = 100

maximumBattery = random.randint(51,100) # A capacidade máxima da bateria é gerada aleatoriamente entre o valor de 51 (potência mínima para o carro percorrer todas as rotas) a 100 (kWh) 

vehicle = Vehicle(vid = vid, owner = owner, licensePlate = licensePlate, moneyCredit = moneyCredit, currentEnergy = currentEnergy, maximumBattery = maximumBattery)

# ---------------------------------------------------------------------------------------------
        
vehicle.savingLoginData(dataFilePath) # Salvando os dados pertinentes
# obs: O arquivo "data.json" tem os dados salvos

#------------------------------------------------------------------------------------------------
# Definindo conexão MQTT 

client_MQTT = mqtt.Client()
#------------------------------------------------------------------------------------------------

# Descobrindo os endereços de contrato através da comunicação MQTT com o servidor

type_subscribe = '1'
vClient = VehicleClient(client_MQTT, vehicle, route, account_number, ID_reservation, type_subscribe)
#------------------------------------------------------------------------------------------------
# Definindo conexão com ganache(Blockchain local)

w3 = Web3(Web3.HTTPProvider(ganache_URL))
account_address = w3.eth.accounts[account_number]

#------------------------------------------------------------------------------------------------

# Início do sistema ->

utility.clearTerminal()

utility.startAnimation() # Função para gerar uma pequena animação na primeira execução do programa
    
print(" Bem vindo(a)! \n")
time.sleep(2)

while(repeat):

    wrongData = True  # Váriavel usada para permitir ou não a entrada no sistema de acordo com os dados de login e senha

    ownerTemplate = User(cpf="", name="", email="", password="")
    vehicleTemplate = Vehicle( vid= "", owner= ownerTemplate, licensePlate= "", moneyCredit= 0.0, currentEnergy= 0, maximumBattery=0)
            
    vehicleTemplate.loadingData(dataFilePath)

    if firstLogin :

        '''
        Os dados são carregados de data.json, a partir da ultima geração de dados ficticios
        obs: O arquivo "data.json" tem os dados salvos caso seja ppreciso conferir os dados para login
        '''
        #------------------------------------------------------------------------------------
                
        while(wrongData):

            print(vehicleTemplate.owner.__dict__) # Printando as informações necessárias para LOGIN
            login = input("\n LOGIN (CPF ou Email): \t ")
            utility.clearTerminal()

            print(vehicleTemplate.owner.__dict__)
            password = input("\n SENHA: ")
            utility.clearTerminal()

            # Conferindo se os dados de login estão corretos
            if (login == vehicleTemplate.owner.cpf or login == vehicleTemplate.owner.email) and password == vehicleTemplate.owner.password:
                    print (" Login realizado com sucesso ! ")
                    time.sleep(3)
                    utility.clearTerminal()
                    wrongData = False
                    firstLogin = False

            else :
                print(" Login ou senha incorreta. Tente novamente !")
                time.sleep(3)
                utility.clearTerminal()
                wrongData = True
         

    wrongActions = True # Variavel de controle de opções de login

    while wrongActions :

        print(" O que deseja fazer? \n")
        reply = input(" Digite: \n\t 1. Fazer reserva \n\t 2. Ver histórico de reservas \n\t 3. Ver informações de conta/veículo \n\t 4. Adicionar crédito \n\t 5. Voltar para o início \n\t 6. Sair do programa \n\t -> ")
        utility.clearTerminal()

        '''
        Apresenta 6 opções de execução do programa:
        
        1. A opção 1 é para realizar a reserva, onde a origem e o destino da viagem é determinado e passado para o servidor via comunicação MQTT
        2. A opção 2 é usada para ver a(s) reserva(s) do veículo já realizadas
        3. A opção 3 é para ver as informações de conta
        4. A opção 4 é para: 1. Iniciar recarga,  2. Finalizar recarga, 3.Ver histórico de recarga
        5. A opção 5 permite voltar para o início do programa
        6. Interrompe totalmente o programa

        obs: Nas opções 1, 2, 3 e 4, o usuário pode decidir voltar pras opções de login ou encerrar o programa

        '''

        if reply == "1" : # Opção 1: Realizar reserva

            wrongCities = True

            while wrongCities:

                utility.clearTerminal()

                print("\t Digite o local de origem: \n")
                origin = input("\t 1 - Vitória da Conquista \n \t 2 - Jequié \n \t 3 - Feira de Santana \n \t 4 - Euclides da Cunha \n \t 5 - Ibó \n \t 6 - Barro \n \t 7 - Jaguaribe \n \t 8 - Russas \n \t 9 - Fortaleza  \n \t  ->")
                
                utility.clearTerminal()

                print("\t Digite o local de destino: \n")
                destination = input("\t 1 - Vitória da Conquista \n \t 2 - Jequié \n \t 3 - Feira de Santana \n \t 4 - Euclides da Cunha \n \t 5 - Ibó \n \t 6 - Barro \n \t 7 - Jaguaribe \n \t 8 - Russas \n \t 9 - Fortaleza  \n \t  ->")
                
                utility.clearTerminal()

                route = utility.defineRoute(origin, destination)

                if route[0] == "false" or route[1] == "false":
                    print("\t Digite dados validos ! ")

                    time.sleep(2)
                    utility.clearTerminal()
                    wrongCities = True

                else:

                    wrongCities = False

                    type_subscribe = '2'
                    vClient = VehicleClient(client_MQTT, vehicle, route, account_number, ID_reservation, type_subscribe)

                    vehicle.showReservations(w3, account_address, contract_reservation_ledger, reservation_ledger_abiFilePath)
                    contract_escrow_address = contracts_addresses["Escrow"]
                    vehicle.payRecharge(w3, account_address, contract_escrow_address, escrow_abi_FilePath)

            
        elif reply == "2" : # Opção 2: Ver reservas

            contract_reservation_ledger = contracts_addresses["ReservationLedger"]

            vehicle.showReservations(w3, account_address, contract_reservation_ledger, reservation_ledger_abiFilePath)
            utility.writeReplyBack(wrongActions, repeat)
        
        elif reply == "3": # Opção 3: Mostrar informações de conta
            
            vehicle.showInformations()
            utility.writeReplyBack(wrongActions, repeat)

        elif reply == "4": # Opção 4: Iniciar ou finalizar reserva

            type_recharge = '0'

            answer_recharge = input("O que deseja fazer ? \n\t 1. Iniciar carregamento \n\t 2. Finalizar carregamento \n\t 3. Ver histórico de recargas -> ")

            if answer_recharge == '1' :

                contract_reservation_ledger_address = contracts_addresses["ReservationLedger"]

                vehicle.showReservations(w3, account_address, contract_reservation_ledger_address, reservation_ledger_abiFilePath)
                
                ID_reservation = input ('\n\t Digite o ID da reserva que deseja iniciar a recarga : \n\t ->')
                
                utility.clearTerminal()
                type_subscribe = '3'
                vClient = VehicleClient(client_MQTT, vehicle, route, account_number, ID_reservation, type_subscribe)
                
                type_recharge = '1'
                vehicle.manageRecharge(type_recharge, ID_reservation)

            elif answer_recharge == '2':
                

                vehicle.showRecharges()

                ID_reservation = input ('Digite o ID da reserva que deseja finalizar a recarga : \n\t ->')

                utility.clearTerminal()

                type_subscribe = '4'
                vClient = VehicleClient(client_MQTT, vehicle, route, account_number, ID_reservation, type_subscribe)

                type_recharge = '2'
                vehicle.manageRecharge(type_recharge, ID_reservation)

            else:
                vehicle.showHistoryRecharges()
                utility.writeReplyBack(wrongActions, repeat)


        elif reply == "5": # Opção 5: Voltar para o início do programa
            wrongActions = False
            repeat = True

        elif reply == "6": # Opção 6: Sair do pragrama
            wrongActions = False
            repeat = False
            utility.endAnimation()

        else:
            utility.clearTerminal()
            print("Digite uma opção válida !")
            time.sleep(2)
            wrongActions = True     