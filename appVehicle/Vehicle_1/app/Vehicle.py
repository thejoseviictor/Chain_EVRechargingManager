from dataclasses import dataclass
from pathlib import Path


from User import User
from VehicleUtility import VehicleUtility

import random
import json
import time

@dataclass
class Vehicle:

    vid: str
    owner: User
    licensePlate: str
    moneyCredit: float

    currentEnergy: int
    maximumBattery : int

    reservations = [] # Guarda as reservas

    utility = VehicleUtility()

    def showInformations(self): # Método para visualização de dados de usúario
         print(f"\n\t Nome completo: {self.owner.name} ")
         print(f"\n\t CPF: {self.owner.cpf}")
         print(f"\n\t Email: {self.owner.email}")
         print(f"\n\t Senha: {self.owner.password}")
         print(f"\n\t ID do veículo: {self.vid}")
         print(f"\n\t Placa: {self.licensePlate}")
         print(f"\n\t Crédito saldo : {self.moneyCredit}")
         

    def showReservations(self): # Método para visualizar todas as reservas efetuadas para o veículo

        if self.reservations :

            print("Reservas efetuadas: \n")

            for r in self.reservations:
                
                print(" ---------------------------------------------- ")
                print(f" ID da reserva: {r['reservationID']} \n")
                print(f" ID do posto: {r['chargingStationID']} \n")
                print(f" ID do ponto de recarga: {r['chargingPointID']} \n")
                print(f" Potência do ponto de carregamento: {r['chargingPointPower']} \n")
                print(f" Preço por kWh: {r['kWhPrice']} \n")
                print(f" ID do veículo: {r['vehicleID']} \n")
                print(f" Início da recarga: {r['startDateTime']} \n")
                print(f" Fim da recarga: {r['finishDateTime']} \n")
                print(f" Duração : {r['duration']} \n")
                print(f" Preço : {r['price']} \n")
                print(" ---------------------------------------------- ")
        
        else:

            print("Não há reservas no momento !")
            time.sleep(3)
   

    def savingLoginData(self, dataFilePath: str): # Método para salvar novos dados gerados na opção "2 - CRIAR CONTA"

            data = {
                
                "cpf" : self.owner.cpf ,
                "name" : self.owner.name ,
                "email" : self.owner.email ,
                "password" : self.owner.password ,
                "vid" : self.vid ,
                "licensePlate" : self.licensePlate ,
                "moneyCredit" : self.moneyCredit ,
                "currentEnergy" : self.currentEnergy ,
                "maximumBattery" : self.maximumBattery

            }

            
            with open(dataFilePath, 'w') as f:
                json.dump(data, f, indent=4)

    def updateCredit(self, dataFilePath: str, value: float, operation: str):

        credit = self.moneyCredit

        if operation == "-":

            credit -= value
            self.moneyCredit = credit
        
        else:
            credit += value
            self.moneyCredit = credit


        with open(dataFilePath, 'r') as f:
            data = json.load(f)
                
        data["moneyCredit"] = credit

        with open(dataFilePath, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Saldo atual: R${self.moneyCredit:.2f}")
        time.sleep(3)
        self.utility.clearTerminal()

    def loadingData(self, dataFilePath: str, reservationsFilePath: str): # Método para carregar dados de conta (dados gerados e salvos anteriormente)

            with open(dataFilePath, 'r') as f:
                data = json.load(f)
                    
            self.owner.cpf = str(data["cpf"])
            self.owner.name = str(data["name"])
            self.owner.email = str(data["email"])
            self.owner.password = str(data["password"]) 
            self.vid = str(data["vid"])
            self.licensePlate = str(data["licensePlate"]) 
            self.moneyCredit = float(data["moneyCredit"])
            self.currentEnergy = int(data["currentEnergy"])
            self.maximumBattery = int(data["maximumBattery"])
            
            with open(reservationsFilePath, 'r') as f:
                listReservations = json.load(f)

            self.reservations = listReservations

    def keepReservations(self, reservationsFilePath: str, newReservations: list[dict]): # Salvando as novas reservas num json "reservations.json"

        with open(reservationsFilePath, 'r') as f:
              data = json.load(f)
        
        for r in newReservations:
            self.reservations.append(r)
            data.append(r)
        
        with open(reservationsFilePath, 'w') as f:
            json.dump(data, f, indent=4)
        
        

        
        
        
