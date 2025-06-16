# Esta Classe é Responsável por Armazenar os Dados dos Pontos de Carregamento dos Postos de Recarga em um Arquivo ".json" no Servidor.
# "Charging Point" é um Local de Carregamento Dentro de um Posto Específico, nos Carros a Combustão São Conhecidos como "Bombas".

import json
import os

class ChargingPointsFile:
    # Inicializando a Classe e seus Atributos:
    def __init__(self, json_file="charging_points.json"):
        os.makedirs("data", exist_ok=True) # Criando a Pasta "data", Se Não Existir.
        self.json_file = os.path.join("data", json_file) # Salvando o Banco de Dados na Pasta "data".
        self.chargingPointsList = [] # Lista dos Pontos de Carregamento.
        self.readChargingPoints() # Recuperando os Dados do Arquivo ".json"

    # Lendo os Pontos de Carregamento no Arquivo ".json":
    def readChargingPoints(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as file:
                    self.chargingPointsList = json.load(file) # Salvando os Dados na Lista.
            except json.JSONDecodeError:
                print(f"Arquivo '{self.json_file}' Está Inválido ou Vazio!\n")
    
    # Procurando um Ponto de Carregamento de um Posto Específico:
    def findChargingPoint(self, chargingPointID: int, chargingStationID: int):
        self.readChargingPoints() # Atualizando a Memória de Execução Com o Banco de Dados em "charging_points.json".
        # Percorrendo a Lista:
        for cp in self.chargingPointsList: # cp = Charging Point - Ponto de Carregamento.
            if cp["chargingPointID"] == chargingPointID:
                if cp["chargingStationID"] == chargingStationID:
                    return cp
        else:
            print(f"Ponto de Carregamento com ID '{chargingPointID}', no Posto de Recarga '{chargingStationID}', Não Foi Encontrado!\n")
            return None

    # Listando os Pontos de Carregamento de um Posto, Cadastrados no Arquivo ".json":
    def listChargingPoints(self, chargingStationID: int):
        self.readChargingPoints() # Atualizando a Memória de Execução Com o Banco de Dados em "charging_points.json".
        searchList = [] # Onde Serão Salvos os Pontos de um Posto Específico.
        for cp in self.chargingPointsList: # cp = Charging Point - Ponto de Carregamento.
            if cp["chargingStationID"] == chargingStationID:
                searchList.append(cp)
        return searchList # Retornando os Pontos de um Posto Específico

    # Salvando a Lista de Pontos de Carregamento no Arquivo ".json":
    def saveChargingPoints(self):
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(self.chargingPointsList, file, indent=4, ensure_ascii=False)

    # Atualizando os Dados de um Ponto de Carregamento de um Posto Específico:
    def updateChargingPoint(self, chargingPointID: int, chargingStationID: int, power: float, kWhPrice: float, availability: str):
        self.readChargingPoints() # Atualizando a Memória de Execução.
        # Percorrendo a Lista:
        for cp in self.chargingPointsList: # cp = Charging Point - Ponto de Carregamento.
            if cp["chargingPointID"] == chargingPointID and cp["chargingStationID"] == chargingStationID:
                cp["power"] = power # Potência do Carregador em kW.
                cp["kWhPrice"] = kWhPrice
                cp["availability"] = availability # "livre", "ocupado" ou "reservado".
                self.saveChargingPoints() # Salvando no Arquivo ".json".
                print(f"Os Dados do Ponto de Carregamento com ID '{chargingPointID}', no Posto de Recarga '{chargingStationID}', Foram Atualizados!\n")
                return True
        # Exibindo a Mensagem de Erro:
        print(f"Ponto de Carregamento com ID '{chargingPointID}', no Posto de Recarga '{chargingStationID}', Não Foi Encontrado!\n")
        return None
    
    # Gerando um ID para Novo Ponto de Carregamento:
    # Os IDs Não Podem Ser Iguais Para o Mesmo Posto de Recarga.
    # IDs Novos: Maior ID + 1.
    def generateChargingPointID(self, chargingStationID: int):
        startID = 1 # Um ID Inicial Que Será Usado Como Comparador.
        for cp in self.chargingPointsList:
            # Percorrendo Todos os Pontos de Carregamento do Mesmo Posto de Recarga Selecionado:
            if cp["chargingStationID"] == chargingStationID:
                # ID Maior ou Igual (Para o Primeiro ID dos Pontos de Carregamento):
                if cp["chargingPointID"] >= startID:
                    startID = cp["chargingPointID"] + 1
        return startID
    
    # Criando um Novo Ponto de Carregamento e Salvando no Arquivo ".json":
    def createChargingPoint(self, chargingStationID: int, power: float, kWhPrice: float, availability: str):
        self.readChargingPoints() # Atualizando a Memória de Execução.
        # Gerando o ID do Ponto de Carregamento:
        chargingPointID = self.generateChargingPointID(chargingStationID)
        # Salvando na Lista:
        self.chargingPointsList.append({
            "chargingPointID": chargingPointID, 
            "chargingStationID": chargingStationID, 
            "power": power, # Potência do Carregador em kW.
            "kWhPrice": kWhPrice,
            "availability": availability # "livre", "ocupado" ou "reservado".
            })
        self.saveChargingPoints() # Salvando no Arquivo ".json".
        print(f"Ponto de Carregamento com ID '{chargingPointID}', no Posto de Recarga '{chargingStationID}', Foi Criado com Sucesso!\n")
        return chargingPointID # Retornando o ID do Ponto de Carregamento Criado.
    
    # Removendo um Ponto de Carregamento do Arquivo ".json":
    def deleteChargingPoint(self, chargingPointID: int, chargingStationID: int):
        self.readChargingPoints() # Atualizando a Memória de Execução.
        for cp in self.chargingPointsList:
            if cp["chargingPointID"] == chargingPointID and cp["chargingStationID"] == chargingStationID:
                self.chargingPointsList.remove(cp)
                self.saveChargingPoints() # Salvando no Arquivo ".json".
                print(f"Ponto de Carregamento com ID '{chargingPointID}', no Posto de Recarga '{chargingStationID}', Foi Removido com Sucesso!\n")
                return True
        print(f"Ponto de Carregamento com ID '{chargingPointID}', no Posto de Recarga '{chargingStationID}', Não Foi Encontrado!\n")
        return None
