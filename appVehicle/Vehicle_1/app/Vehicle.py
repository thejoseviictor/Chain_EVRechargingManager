from dataclasses import dataclass

from pathlib import Path


from User import User
from VehicleUtility import VehicleUtility

import datetime # Biblioteca para tratar datas e horarios
import random
import json
import time

from web3 import Web3

@dataclass
class Vehicle:

    def __init__(self, vid, owner, licensePlate, moneyCredit, currentEnergy, maximumBattery):
        self.vid = vid
        self.owner = owner
        self.licensePlate = licensePlate
        self.moneyCredit = moneyCredit

        self.currentEnergy = currentEnergy
        self.maximumBattery = maximumBattery

        self.reservationsList = [] # Guarda as reservas
        self.recharge_list = [] # Guarda os IDs de reservas que estão em recarga
        self.history_recharges = []

        self.utility = VehicleUtility()

    def showInformations(self): # Método para visualização de dados de usúario
         print(f"\n\t Nome completo: {self.owner.name} ")
         print(f"\n\t CPF: {self.owner.cpf}")
         print(f"\n\t Email: {self.owner.email}")
         print(f"\n\t Senha: {self.owner.password}")
         print(f"\n\t ID do veículo: {self.vid}")
         print(f"\n\t Placa: {self.licensePlate}")
         print(f"\n\t Crédito saldo : {self.moneyCredit}")
         print(f"\n\t Bateria atual(kWh) : {self.currentEnergy}%")
         print(f"\n\t Capacidade total da bateria(kWh) : {self.maximumBattery}%")

    def payRecharge(self, w3, account_address, contract_address, abiFilePath):

        with open(abiFilePath, 'r') as f:
            abi = json.load(f)
        
        w3.eth.contract(address=contract_address, abi=abi)

        contractAddress = w3.to_checksum_address(contract_address)

        escrow_contract = w3.eth.contract(address=contractAddress, abi=abi)

        for r in self.reservationsList:
            
            tx_hash = escrow_contract.functions.depositFunds(r["reservationID"]).transact({
            'from': account_address, # Endereço do Carro
            'value': int( r["price"] ), # Preço em "wei", Presente nas Informações da Reserva
            "nonce": w3.eth.get_transaction_count(account_address),
            'gasPrice': w3.eth.gas_price,
            "gas": 125000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)


    def showReservations(self, w3, account_address, contract_address, abiFilePath): # Método para visualizar todas as reservas efetuadas para o veículo na blockchain
        
        current_list = []

        with open(abiFilePath, 'r') as f:
            abi = json.load(f)
        
        w3.eth.contract(address=contract_address, abi=abi)
         
        contractAddress = w3.to_checksum_address(contract_address)

        contract = w3.eth.contract(address=contractAddress, abi=abi)

        reservations = contract.functions.getReservationsByCustomer(account_address).call()

        for res in reservations:
            
            res_dict = {
                "reservationID": res[0],
                "chargingStationID": res[1],
                "chargingPointID": res[2],
                "cityCodename": res[3],
                "companyName": res[4],
                "chargingPointPower": res[5],
                "kWhPrice": res[6],
                "startTimestamp": datetime.datetime.fromtimestamp(res[7]).isoformat(),
                "finishTimestamp": datetime.datetime.fromtimestamp(res[8]).isoformat(),
                "price": res[9], 
                "customer": res[10],
                "status": res[11]
            }
            
            current_list.append(res_dict)
        
        self.reservationsList = current_list

        for r in self.reservationsList:

            print(r) 
            print('----------------------------------------------------------')

    
    def manageRecharge(self, type_recharge: str, ID_reservation: str):
        
        if type_recharge == '1':
            self.recharge_list.append(ID_reservation)
        
        else:
            for r, id in enumerate(self.recharge_list):
                if ID_reservation == id:
                    self.history_recharges.append(id)
                    self.recharge_list.remove(id)

    def showRecharges(self):

        print('Lista de recargas (iniciadas) : \n')

        for r, id in enumerate(self.recharge_list):
            print(f'\n\t ID de recarga {r+1} : {id}')
            print('-----------------------------------------------------')
    
    def showHistoryRecharges(self):
        print('Histórico de recargas (finalizadas): \n')

        for r, id in enumerate(self.history_recharges):
            print(f'\n\t ID de recarga {r+1} : {id}')
            print('-----------------------------------------------------')
        
