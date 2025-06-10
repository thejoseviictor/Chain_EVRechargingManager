// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReservationLedger {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Status da Reserva:
    enum Status {PENDING, CONFIRMED, PAYED, CANCELLED}

    // Dados da Reserva:
    struct Reservation {
        uint256 reservationID;
        uint256 chargingStationID;
        uint256 chargingPointID;
        string cityName;
        string cityCodename;
        string companyName;
        uint256 chargingPointPower; // Potência do Carregador em kW.
        uint256 kWhPrice; // Em "wei", Menor Unidade de Valor do Ethereum.
        uint256 vehicleID;
        uint256 startDateTime; // Converter ISO para "timestamp".
        uint256 finishDateTime;
        uint256 durationHours; // Duração em Horas.
        uint256 price; // Preço em "wei".
        address payable customer; // Endereço da Carteira do Cliente, Para Pagamentos.
        Status status;
    }

    // Dados da Transação:
    struct TransactionRecord {
        uint256 transactionID;
        uint256 reservationID;
        uint256 price; // Preço da Transação em "wei".
        address payer; // Endereço da Carteira que Efetuou o Pagamento.
        bool paid; // Indica Se o Pagamento foi Confirmado.
        uint256 transactionTimestamp;
    }

    // Mapeamentos:
    mapping(uint256 => Reservation) public reservations;
    mapping(uint256 => TransactionRecord) public transactionRecords;
    mapping(address => bool) public authorizedRechargingServers;

    // Contadores de IDs:
    uint256 public nextReservationID;
    uint256 public nextTransactionID;

    // Eventos para Notificações:
    event ReservationCreated(
        uint256 indexed reservationID,
        uint256 indexed chargingStationID,
        uint256 indexed chargingPointID,
        address indexed customer,
        uint256 startDateTime,
        uint256 price
    );
    event ReservationStatusUpdated(uint256 indexed reservationID, Status status);
    event TransactionRecorded(
        uint256 indexed transactionID,
        uint256 indexed reservationID,
        uint256 price,
        address indexed payer
    );

    // Modificadores:
    // Apenas o Administrador Pode Adicionar Servidores de Postos Autorizados:
    modifier onlyOwner() {
        require(msg.sender == owner, "Apenas o Administrador Pode Executar Esta Ação!");
        _;
    }
    // Para Criar, Confirmar, Cancelar ou Concluir Reservas, ou Registrar Transações: Apenas um dos Servidores de Carregamento ou Administrador.
    modifier onlyServerOrOwner() {
        require(authorizedRechargingServers[msg.sender] || msg.sender == owner, "Apenas um Dos Servidores de Carregamento ou Administrador Pode Executar Esta Ação!");
        _;
    }

    // Construtor:
    constructor() {
        owner = msg.sender; // Define o Deployer do Contrato Como o Owner.
        nextReservationID = 1;
        nextTransactionID = 1;
    }

    // Função para Autorizar um Servidor de Posto de Carregamento:
    function authorizeRechargingServer(address _server) public onlyOwner {
        authorizedRechargingServers[_server] = true;
    }

    // Criando uma Nova Reserva:
    function createReservation(
        uint256 _chargingStationID,
        uint256 _chargingPointID,
        string memory _cityName,
        string memory _cityCodename,
        string memory _companyName,
        uint256 _chargingPointPower,
        uint256 _kWhPrice,
        uint256 _vehicleID,
        uint256 _startDateTime,
        uint256 _finishDateTime,
        uint256 _durationHours,
        address _customerAddress // Endereço da Carteira do Cliente.
    ) public onlyServerOrOwner returns (uint256) {
        // Calculando o Preço: Potência do Carregador * Duração em Horas * Preço kWh do Carregador
        uint256 price = _chargingPointPower * _durationHours * _kWhPrice;

        // Criando a Reserva:
        uint256 newReservationID = nextReservationID;
        reservations[newReservationID] = Reservation({
            reservationID: newReservationID,
            chargingStationID: _chargingStationID,
            chargingPointID: _chargingPointID,
            cityName: _cityName,
            cityCodename: _cityCodename,
            companyName: _companyName,
            chargingPointPower: _chargingPointPower,
            kWhPrice: _kWhPrice,
            vehicleID: _vehicleID,
            startDateTime: _startDateTime,
            finishDateTime: _finishDateTime,
            durationHours: _durationHours,
            price: price,
            customer: payable(_customerAddress),
            status: Status.PENDING
        });

        // Incrementando o ID Para a Próxima Reserva:
        nextReservationID++;

        // Emitindo a Notificação:
        emit ReservationCreated(
            newReservationID,
            _chargingStationID,
            _chargingPointID,
            _customerAddress,
            _startDateTime,
            price
        );

        // Retornando o ID da Reserva:
        return newReservationID;
    }

    // Confirmando uma Reserva:
    function confirmReservation(uint256 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Inválido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Não é Possível Confirmar uma Reserva Cancelada!");
        require(reservations[_reservationID].status == Status.PENDING, "Não é Possível Confirmar uma Reserva Já Confirmada ou Finalizada!");
        
        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.CONFIRMED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Cancelando uma Reserva Existente:
    function cancelReservation(uint256 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Inválido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Não é Possível Cancelar uma Reserva Já Cancelada!");
        require(reservations[_reservationID].status != Status.PAYED, "Não é Possível Cancelar uma Reserva Paga!");
        require(block.timestamp < reservations[_reservationID].startDateTime, "Não é Possível Cancelar uma Reserva Já Iniciada!");

        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.CANCELLED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    /**
     * Registrando, Imutavelmente, uma Transação de Pagamento Auditável de Reserva no Ledger.
     * Supõe-se que o Pagamento Real (Transferência de ETH/Tokens) Ocorreu.
     * Estamos Apenas Registrando a Operação.
     */
    function recordTransaction(
        uint256 _reservationID,
        address _payer, // Endereço da Carteira Pagante.
        bool _paid // Status de Pagamento: "true" ou "false".
    ) public onlyServerOrOwner returns (uint256) {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Inválido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Não é Possível Registrar o Pagamento de uma Reserva Cancelada!");
        require(reservations[_reservationID].status != Status.PENDING, "Não é Possível Registrar o Pagamento de uma Reserva Pendente!");
        require(reservations[_reservationID].status != Status.PAYED, "Não é Possível Registrar o Pagamento de uma Reserva Paga!");

        // Criando a Transação:
        uint256 newTransactionID = nextTransactionID;
        transactionRecords[newTransactionID] = TransactionRecord({
            transactionID: newTransactionID,
            reservationID: _reservationID,
            price: reservations[_reservationID].price,
            payer: _payer,
            paid: _paid,
            transactionTimestamp: block.timestamp
        });

        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.PAYED;

        // Incrementando o ID Para a Próxima Transação:
        nextTransactionID++;

        // Emitindo a Notificação da Transação:
        emit TransactionRecorded(
            newTransactionID,
            _reservationID,
            reservations[_reservationID].price,
            _payer
        );

        // Emitindo a Notificação da Reserva:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);

        // Retornando o ID da Transação:
        return newTransactionID;
    }

    // Função para Auditar uma Reserva:
    function getReservation(uint256 _reservationID) public view returns (
        uint256 reservationID,
        uint256 chargingStationID,
        uint256 chargingPointID,
        string memory cityName,
        string memory cityCodename,
        string memory companyName,
        uint256 chargingPointPower,
        uint256 kWhPrice,
        uint256 vehicleID,
        uint256 startDateTime,
        uint256 finishDateTime,
        uint256 durationHours,
        uint256 price,
        address customer,
        Status status
    ) {
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Inválido!");
        Reservation storage r = reservations[_reservationID];
        return (
            r.reservationID,
            r.chargingStationID,
            r.chargingPointID,
            r.cityName,
            r.cityCodename,
            r.companyName,
            r.chargingPointPower,
            r.kWhPrice,
            r.vehicleID,
            r.startDateTime,
            r.finishDateTime,
            r.durationHours,
            r.price,
            r.customer,
            r.status
        );
    }

    // Função para Auditar uma Transação:
    function getTransactionRecord(uint256 _transactionID) public view returns (
        uint256 transactionID,
        uint256 reservationID,
        uint256 price,
        address payer,
        bool paid,
        uint256 transactionTimestamp
    ) {
        require(transactionRecords[_transactionID].transactionID != 0, "ID de Transação Não Encontrado!");
        TransactionRecord storage tr = transactionRecords[_transactionID];
        return (
            tr.transactionID,
            tr.reservationID,
            tr.price,
            tr.payer,
            tr.paid,
            tr.transactionTimestamp
        );
    }
}
