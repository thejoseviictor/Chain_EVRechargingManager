# Esta Classe é Responsável por Armazenar os Dados dos Postos de Recarga da Empresa em um Arquivo ".json" no Servidor.
# "Charging Station" Representa as Unidades (Postos) de uma Empresa Específica.

import json
import os

class ChargingStationsFile:
    # Inicializando a Classe e seus Atributos:
    def __init__(self, json_file="charging_stations.json"):
        os.makedirs("data", exist_ok=True) # Criando a Pasta "data", Se Não Existir.
        self.json_file = os.path.join("data", json_file) # Salvando o Banco de Dados na Pasta "data".
        self.chargingStationsList = [] # Lista dos Postos de Recarga.
        self.readChargingStations() # Recuperando os Dados do Arquivo ".json"

    # Lendo os Pontos de Recarga no Arquivo ".json":
    def readChargingStations(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as file:
                    self.chargingStationsList = json.load(file) # Salvando os Dados na Lista.
            except json.JSONDecodeError:
                print(f"Arquivo '{self.json_file}' Está Inválido ou Vazio!\n")
    
    # Procurando um Posto de Recarga Específico:
    def findChargingStation(self, chargingStationID: int):
        self.readChargingStations() # Atualizando a Memória de Execução Com o Banco de Dados em "charging_stations.json".
        # Percorrendo a Lista:
        for cs in self.chargingStationsList:
            if cs["chargingStationID"] == chargingStationID:
                return cs
        else:
            print(f"Posto de Recarga com ID '{chargingStationID}' Não Foi Encontrado!\n")
            return None

    # Listando os Postos de Recarga Cadastrados no Arquivo ".json":
    def listChargingStations(self):
        self.readChargingStations() # Atualizando a Memória de Execução.
        return self.chargingStationsList

    # Salvando a Lista no Arquivo ".json":
    def saveChargingStations(self):
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(self.chargingStationsList, file, indent=4, ensure_ascii=False)

    # Atualizando a Cidade de um Posto de Recarga Específico:
    def updateChargingStation(self, chargingStationID: int, city_codename: str, city_name: str):
        self.readChargingStations() # Atualizando a Memória de Execução.
        for cs in self.chargingStationsList:
            if cs["chargingStationID"] == chargingStationID:
                cs["city_codename"] = city_codename
                cs["city_name"] = city_name
                self.saveChargingStations() # Salvando no Arquivo ".json".
                print(f"A Cidade do Posto de Recarga com ID '{chargingStationID}' Foi Alterada para '{city_name}' com Sucesso!\n")
                return True
        # Exibindo a Mensagem de Erro:
        print(f"Posto de Recarga com ID '{chargingStationID}' Não Foi Encontrado!\n")
        return None
    
    # Gerando um ID para Novo Posto de Recarga:
    # Os IDs Não Podem Ser Iguais.
    # IDs Novos: Maior ID + 1.
    def generateChargingStationID(self):
        startID = 1 # Um ID Inicial Que Será Usado Como Comparador.
        for cs in self.chargingStationsList:
            # ID Maior ou Igual (Para o Primeiro ID dos Postos de Recarga):
            if cs["chargingStationID"] >= startID:
                startID = cs["chargingStationID"] + 1
        return startID
    
    # Criando um Novo Posto de Recarga e Salvando no Arquivo ".json":
    def createChargingStation(self, city_codename: str, city_name: str):
        self.readChargingStations() # Atualizando a Memória de Execução.
        chargingStationID = self.generateChargingStationID()
        # Salvando na Lista:
        self.chargingStationsList.append({
            "chargingStationID": chargingStationID, 
            "city_codename": city_codename, 
            "city_name": city_name})
        self.saveChargingStations() # Salvando no Arquivo ".json".
        print(f"Posto de Recarga com ID '{chargingStationID}' em '{city_name}' Foi Salvo com Sucesso!\n")
        return chargingStationID # Retornando o ID do Posto de Recarga Criado.
    
    # Removendo um Posto do Arquivo ".json":
    def deleteChargingStation(self, chargingStationID: int):
        self.readChargingStations() # Atualizando a Memória de Execução.
        for cs in self.chargingStationsList:
            if cs["chargingStationID"] == chargingStationID:
                self.chargingStationsList.remove(cs)
                self.saveChargingStations() # Salvando no Arquivo ".json".
                print(f"Posto de Recarga com ID '{chargingStationID}' Foi Removido com Sucesso!\n")
                return True
        print(f"Posto de Recarga com ID '{chargingStationID}' Não Foi Encontrado!\n")
        return None
