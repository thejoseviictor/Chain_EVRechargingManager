# Chain_EVRechargingManager

## Arquitetura de Sistema dos Servidores:
O funcionamento da arquitetura dos servidores se manteve semelhante ao projeto anterior, do repositório “DistributedElectricCarsRechargingManager”. Porém, as reservas, recargas e transações precisam ter seus blocos aprovados e inseridos na blockchain, do tipo “ledger”, permitindo que os dados sejam imutáveis - apenas o “status” da informação pode ser alterado - e auditáveis.
<br><br>Além disso, foi adicionada a entidade “Owner” que é responsável por executar o “deploy” dos contratos, autorizar contas Ganache de servidores a fazer operações na blockchain e liberar o pagamento das recargas a seus respectivos servidores e empresas.

## Cenário de Funcionamento das Transações:
O cliente do veículo solicitará e receberá as reservas através dos tópicos MQTT;
<br><br>O cliente do veículo depositará o pagamento das reservas, individualmente, através dos identificadores e dos valores delas na blockchain;
<br><br>O cliente do veículo solicitará o início de uma sessão de carregamento, através do identificador da reserva, no tópico MQTT.
<br><br>A solicitação do tópico MQTT será encaminhada para a blockchain, através de um dos servidores das empresas, que verificará se o pagamento foi depositado para a reserva em específico, se sim, a recarga será liberada.
<br><br>O cliente do veículo solicitará a finalização de uma sessão de carregamento, através do identificador da reserva, no tópico MQTT.
<br><br>A solicitação do tópico MQTT será encaminhada para a blockchain, através de um dos servidores das empresas, que liberará o pagamento da reserva da recarga encerrada para a carteira da devida empresa que prestou o serviço.

## Passo-a-Passo de Execução da Blockchain e Servidores:
Cada entidade deve rodar em seu próprio container Docker e suas imagens podem ser geradas através do arquivo “app/docker-compose.yml” através do seguinte comando: “docker-compose build”.
<br><br>Após gerar as imagens, é possível executar cada entidade através do seguinte comando: “docker-compose up [service]”
<br><br>Ordem de execução dos containers das entidades: ganache, owner, mosquitto, ecocharge, eflux, voltpoint.
<br><br>Se os servidores forem executados em computadores diferentes, indique para cada um deles os endereços IP dos outros, editando as variáveis de ambiente nos arquivos “.env” de cada servidor.
<br><br>Para o funcionamento adequado do sistema, o “deploy” dos contratos deve ser executado pelo cliente “owner”.

## Tópicos MQTT “Subscriber” dos Servidores:
"vehicle/contracts_addresses/server”, para indicar os endereços dos contratos no Ganache.
<br><br>"vehicle/create_reservations/server", para agendar as reservas.
<br><br>"vehicle/start_charging_session/server", para iniciar uma sessão de carregamento.
<br><br>"vehicle/end_charging_session/server", para finalizar uma sessão de carregamento.

## Tópicos MQTT “Publisher” dos Servidores:
“server/contracts_addresses/vehicle”, para indicar os endereços dos contratos no Ganache.
<br><br>"server/create_reservations/vehicle", para retornar os identificadores das reservas agendadas, ou erro no agendamento.
<br><br>"server/start_charging_session/vehicle", para retornar sucesso ou falha, ao iniciar uma sessão de carregamento.
<br><br>"server/end_charging_session/vehicle", para retornar sucesso ou falha, ao finalizar uma sessão de carregamento.
