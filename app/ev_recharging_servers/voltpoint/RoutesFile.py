# Esta Classe é Responsável por Armazenar e Manipular as Rotas em um Arquivo ".json" no Servidor.

import json
import os

class RoutesFile:
    # Inicializando a Classe e seus Atributos:
    def __init__(self, json_file="routes.json"):
        os.makedirs("data", exist_ok=True) # Criando a Pasta "data", Se Não Existir.
        self.json_file = os.path.join("data", json_file) # Salvando o Banco de Dados na Pasta "data".
        self.routesList = [] # Lista de Rotas.
        self.readRoutes() # Recuperando os Dados do Arquivo ".json".

    # Lendo as Rotas no Banco de Dados:
    def readRoutes(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as file:
                self.routesList = json.load(file) # Salvando os Dados do Arquivo ".json" na Lista.
    
    # Descobrindo Uma Rota da Cidade de Partida para Destino:
    def findRoute(self, departureCityCodename: str, arrivalCityCodename: str):
        self.readRoutes() # Atualizando a Memória de Execução Com o Banco de Dados em "routes.json".
        allowAppend = False # Deve Esperar Até Encontrar a Cidade de Partida.
        resultedRoute = [] # Salvará os Apelidos da Cidades Onde o Veículo Deve Passar.
        # Percorrendo as Rotas e Suas Cidades:
        for route in self.routesList:
            for city in route["cities"]:
                # Verificando Se Encontrou a Cidade de Partida:
                if city["codename"] == departureCityCodename:
                    allowAppend = True # Permitindo Que Novas Cidades Sejam Salvas.
                # Salvando as Cidades do Percurso, Se Encontrou a Cidade de Partida:
                if allowAppend:
                    resultedRoute.append(city)
                    # Se Achou a Última Cidade, Retorne!
                    if city["codename"] == arrivalCityCodename:
                        return resultedRoute
            allowAppend = False # Restaurando a Permissão de Salvamento.
            resultedRoute = [] # Limpando a Lista para Percorrer uma Nova Rota.
        print(f"Não Foi Encontrada uma Rota Que Percorre as Cidades!\n")
        return None

    # Salvando a Lista de Rotas no Banco de Dados:
    def saveRoutes(self):
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(self.routesList, file, indent=4, ensure_ascii=False)

    # Atualizando as Cidades de uma Rota Específica:
    def updateRoute(self, routeID: int, cities: list):
        self.readRoutes() # Atualizando a Memória de Execução.
        # Percorrendo a Lista de Rotas:
        for route in self.routesList:
            if route["routeID"] == routeID:
                route["cities"] = cities # Atualizando as Cidades.
                self.saveRoutes() # Atualizando o Arquivo ".json".
                print(f"Os Dados da Rota Com ID '{routeID}' Foram Atualizados!\n")
                return True
        # Exibindo a Mensagem de Erro:
        print(f"A Rota com ID '{routeID}' Não Foi Encontrada!\n")
        return None
    
    # Gerando um ID Único para uma Nova Rota:
    def generateRouteID(self):
        startID = 1 # Um ID Inicial Que Será Usado Como Comparador.
        for route in self.routesList:
            # ID Maior ou Igual:
            if route["routeID"] >= startID:
                startID = route["routeID"] + 1 # ID Novo: Maior ID + 1.
        return startID
    
    # Calculando a Distância Máxima Entre as Cidades da Rota, Que Será a Autonomia Mínima para os Veículos Trafegarem:
    def minimumRouteAutonomy(self, cities: list):
        routeCitiesCount = len(cities) # Quantidade de Cidades na Rota.
        if routeCitiesCount <= 1:
            return 0 # A Rota Tem Apenas uma Cidade.
        else:
            maximumDistanceBetweenCities = cities[1]["location"] - cities[0]["location"] # Considerando Inicialmente Que a Maior Distância Está Entre as Cidades "1" e "2".
            for city in range(routeCitiesCount-1):
                distanceBetweenCities = cities[city+1]["location"] - cities[city]["location"] # Distância Entre a Cidade Atual e a Próxima.
                if distanceBetweenCities > maximumDistanceBetweenCities:
                    maximumDistanceBetweenCities = distanceBetweenCities # Achou uma Distância Maior.
            return maximumDistanceBetweenCities
    
    # Criando uma Nova Rota no Arquivo ".json":
    # Formatação da Lista das Cidades: [{"codename": str, "name": str, "location": int, "company": str}]
    def createRoute(self, cities: list):
        self.readRoutes() # Atualizando a Memória de Execução.
        # Gerando o ID da Rota:
        routeID = self.generateRouteID()
        # Salvando na Lista:
        self.routesList.append({
            "routeID": routeID,
            "cities": cities
            })
        self.saveRoutes() # Atualizando o Arquivo ".json".
        print(f"A Rota Foi Criada Com ID '{routeID}'!\n")
        return True
    
    # Removendo uma Rota do Banco de Dados:
    def deleteRoute(self, routeID: int):
        self.readRoutes() # Atualizando a Memória de Execução.
        for route in self.routesList:
            if route["routeID"] == routeID:
                self.routesList.remove(route)
                self.saveRoutes() # Salvando no Arquivo ".json".
                print(f"A Rota Com ID '{routeID}' Foi Removida!\n")
                return True
        print(f"A Rota Com ID '{routeID}' Não Foi Encontrada!\n")
        return None
