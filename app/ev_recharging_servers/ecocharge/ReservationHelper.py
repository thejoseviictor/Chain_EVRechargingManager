# Biblioteca de Operações em Parâmetros de Reservas:

import datetime
from ChargingPointsFile import ChargingPointsFile
from ReservationsFile import ReservationsFile
from RoutesFile import RoutesFile

# Escolhendo os Postos de Recarga Onde o Veículo Deve Fazer Reservas:
def chooseChargingStations(vehicleID: int, departureCityCodename: str, arrivalCityCodename: str, actualBatteryPercentage: int, batteryCapacity: float):
    routesFile = RoutesFile() # Lendo as Rotas no Banco de Dados.
    # Escolhendo uma Rota da Cidade de Partida para a Cidade de Destino:
    if departureCityCodename and arrivalCityCodename:
        # "resultedRoute" Vai Orientar as Cidades Onde o Veículo Deve Passar para Chegar ao Destino.
        resultedRoute = routesFile.findRoute(departureCityCodename, arrivalCityCodename) # Lista Com a Rota Encontrada.
    if not resultedRoute:
        print(f"Erro: Nenhum Rota Foi Encontrada de '{departureCityCodename}' para '{arrivalCityCodename}' para o Veículo '{vehicleID}'!\n")
        return None # Não Encontrou uma Rota.
    else:
        if not batteryCapacity:
            print(f"Erro: Sem Informação Sobre a Capacidade de Bateria do Veículo '{vehicleID}' em kWh!\n")
            return None # Não Informou a Capacidade da Bateria em kWh.
        elif not actualBatteryPercentage:
            print(f"Erro: Sem Informação Sobre a Porcentagem Atual de Bateria do Veículo '{vehicleID}'!\n")
            return None # Não Informou a Porcentagem Atual de Bateria do Veículo.
        else:
            reservationsRoute = [] # As Cidades Onde o Veículo Deverá Parar para Recarregar, de Acordo Com Sua Autonomia.
            averageConsumption = 20 # Consumo Médio Por 100 km (Geralmente é 20 kWh / 100 km, no Brasil - Referência: Mercedes-Benz).
            totalBatteryAutonomy = (batteryCapacity * 100) / averageConsumption # Autonomia da Bateria em Km (Quilômetros).
            currentBatteryAutonomy = (totalBatteryAutonomy * actualBatteryPercentage) / 100 # Autonomia para a Porcentagem Atual de Bateria.
            routeCitiesCount = len(resultedRoute) # Quantidade de Cidades na Rota Encontrada.

            # Verificando Se a Autonomia Total (Com 100% de Bateria) do Veículo Permite Percorrer Entre Todas as Cidades da Rota:
            minimumRouteAutonomy = routesFile.minimumRouteAutonomy(resultedRoute) # Autonomia Mínima da Rota Encontrada.
            if minimumRouteAutonomy > totalBatteryAutonomy:
                print(f"Erro: O Veículo '{vehicleID}' Não Tem Autonomia Total Mínima para Viajar Entre as Cidades da Rota'\n")
                return None
            
            # Não Sabemos a Velocidade dos Veículos, Então Definimos a Distância Mínima Que Todos os Veículos Conseguem Percorrer em Uma Hora.
            minimumDistancePerHour = 50 # Distância Mínima = Velocidade Mínima em km/h.

            lastReservationKey = 0 # A Chave da Cidade Onde a Última Reserva Está Prevista.

            # Calculando Onde as Reservas Devem Ser Feitas:
            # Como Funciona:
            # 1. Calcule a Distância da Cidade Atual Até a Próxima Cidade.
            # 2. Verifique Se Essa Distância é Maior do Que a Autonomia Atual.
            # 2.1. Se Sim, o Veículo Deve Recarregar na Cidade Atual Antes de Prosseguir.
            # 3. Decremente a Autonomia Atual pela Distância Entre as Cidades, Para Descobrir Com Quanto de Autonomia Ele Chegará na Próxima Cidade.
            # 4. Refaça os Passos Anteriores, Até Chegar a Última Cidade da Rota.
            for city in range(routeCitiesCount-1):
                distanceBetweenCities = resultedRoute[city+1]["location"] - resultedRoute[city]["location"] # Distância Entre a Cidade Atual e a Cidade Próxima.
                if distanceBetweenCities > currentBatteryAutonomy: # Situação de Recarga.
                    # Calculando a Distância Entre a Cidade da Última Reserva e a Cidade Atual:
                    distanceFromLastReservationCity = resultedRoute[city]["location"] - resultedRoute[lastReservationKey]["location"]
                    # Calculando o Tempo Necessário, em Horas, para Alcançar Essa Cidade, de Acordo com a Posição da Cidade da Reserva Anterior.
                    # Tempo para Alcançar = (Distância da Cidade da Última Reserva / Distância Mínima de Deslocamento por Hora) + Tempo para Alcançar da Cidade da Última Reserva.
                    try:
                        # Será Usado para Calcular a Data e Hora de Ínicio da Reserva:
                        # Deve Ser Somada a Duração da Reserva Anterior, Através do Arquivo "Server.py"
                        timeToReach = (distanceFromLastReservationCity / minimumDistancePerHour) + resultedRoute[lastReservationKey]["timeToReach"]
                    except KeyError: # Se For a Primeira Cidade para Reserva:
                        timeToReach = distanceFromLastReservationCity / minimumDistancePerHour
                    actualBatteryPercentage = (currentBatteryAutonomy * 100) / totalBatteryAutonomy # Atualizando a Porcentagem de Bateria ao Chegar Nesta Cidade.
                    # Salvando as Informações de Tempo para Alcançar e Porcentagem de Bateria Atual:
                    resultedRoute[city]["timeToReach"] = timeToReach
                    resultedRoute[city]["actualBatteryPercentage"] = actualBatteryPercentage
                    # Adicionando a Cidade Atual na Lista de Cidades Onde Reservar:
                    reservationsRoute.append(resultedRoute[city])
                    currentBatteryAutonomy = totalBatteryAutonomy # Resetando a Autonomia do Veículo, Pois Haverá uma Recarga Completa.
                    lastReservationKey = city # Salvando a Posição da Chave Desta Cidade, Como a Cidade da Última Reserva.
                currentBatteryAutonomy -= distanceBetweenCities # Autonomia Que o Veículo Terá ao Chegar na Próxima Cidade.
            
            # Retornando a Lista Com as Cidades Onde Devem Ser Feitas Reservas:
            if reservationsRoute:
                return reservationsRoute
            # Retornando None, Se Não Houver Necessidade de Reservas:
            else:
                return None

# Escolher um Ponto de Carregamento para o Veículo:
def chooseChargingPoint(chargingStationID: int):
    # Calcular o Ponto de Carregamento Sem Reservas ou Com Reserva Que Acaba Mais Cedo:
    chargingPointsList = ChargingPointsFile() # Lendo Dados do Arquivo ".json".
    cp = chargingPointsList.listChargingPoints(chargingStationID) # Listando Todos os Pontos de Carregamento do Posto de Recarga.
    reservationsList = ReservationsFile() # Lendo Dados do Arquivo ".json".
    reservations = reservationsList.listReservations(chargingStationID) # Listando Todos as Reservas Para o Posto de Recarga.
    chargingPointID = None # Inicializando o ID do Ponto de Carregamento a Ser Escolhido.
    # Verificando Se Existem Pontos de Carregamento para o Posto de Recarga, Cadastrados no Banco de Dados:
    if cp:
        # Escolhendo o Ponto de Carregamento, Se Houverem Reservas Cadastradas Naquele Posto:
        if reservations:
            # Percorrendo a Lista de Pontos de Carregamento e Reservas para Encontrar um Ponto de Carregamento Sem Reserva:
            for point in cp:
                found = False # Vai Indicar Se Foi Encontrada Alguma Reserva Para o Ponto de Carregamento.
                for rs in reservations:
                    # Se Achar Pelo Menos uma Reserva Para o Ponto de Carregamento, Encerre o Loop de Reservas e Pule Para o Próximo Ponto:
                    if point["chargingPointID"] == rs["chargingPointID"]:
                        found = True
                        break
                # Se Não Achar Pelo Menos uma Reserva Para o Ponto de Carregamento, Ele Será o Selecionado Para uma Nova Reserva:
                if not found:
                    chargingPointID = point["chargingPointID"]
                    break
            # Encontrando o Ponto de Carregamento Que Vai Ficar Livre Mais Cedo, Se um Ponto Vazio Não Foi Encontrado Anteriormente:
            if not chargingPointID:
                latestFinishingReservation = None # Vai Salvar a Célula com os Dados da Reserva Que Vai Acabar Mais Cedo.
                latestDate = None # Usado Para Comparar Com as Datas de Finalização das Reservas.
                # Percorrendo a Lista de Reservas:
                for rs in reservations:
                    endTime = datetime.datetime.fromisoformat(rs["finishDateTime"]) # Salvando a Data de Finalização em Formato DateTime.
                    if latestDate is None or endTime < latestDate: # Comparando a Data de Finalização da Reserva Atual Com a Mais Recente Até o Momento.
                        latestDate = endTime # Salvando a Data, Se For Mais Recente.
                        latestFinishingReservation = rs # Salvando a Célula da Reserva.
                chargingPointID = latestFinishingReservation["chargingPointID"] # Copiando o ID do Ponto de Carregamento da Reserva Que Vai Acabar Mais Cedo.
            # Retornando o ID do Ponto de Carregamento Encontrado:
            return chargingPointID
        # Retornando o ID do Primeiro Ponto de Carregamento, Se Não Houverem Reservas:
        else:
            chargingPointID = cp[0]["chargingPointID"]
            return chargingPointID
    # Retorno de Erro, Se Não Houverem Pontos de Carregamento:
    else:
        return None
