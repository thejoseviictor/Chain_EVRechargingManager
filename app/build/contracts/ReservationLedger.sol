// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

// Importando as Dependências dos Outros Contratos:
import "./AuthorizedServers.sol";

contract ReservationLedger {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Referência ao Contrato "AuthorizedServers":
    AuthorizedServers public authorizedServers;

    // Status da Reserva:
    enum Status {PENDING, CONFIRMED, PAYED, CANCELLED}

    // Dados da Reserva:
    struct Reservation {
        uint256 reservationID;
        uint256 chargingStationID;
        uint256 chargingPointID;
        string cityCodename;
        string companyName;
        uint256 chargingPointPower; // Potência do Carregador em kW.
        uint256 kWhPrice; // Em "wei", Menor Unidade de Valor do Ethereum.
        uint256 startTimestamp;
        uint256 finishTimestamp;
        uint256 price; // Preço em "wei".
        address payable customer; // Endereço da Carteira do Cliente, Para Pagamentos.
        Status status;
    }

    // Mapeamentos:
    mapping(uint256 => Reservation) public reservations;
    mapping(address => uint256[]) private customerReservationIDs;  

    // Contadores de IDs:
    uint256 public nextReservationID;

    // Eventos para Notificações:
    event ReservationCreated(
        uint256 indexed reservationID,
        address customer,
        string cityCodename,
        uint256 price
    );
    event ReservationStatusUpdated(uint256 indexed reservationID, Status status);

    // Modificador:
    modifier onlyServerOrOwner() {
        require(authorizedServers.isAuthorizedRechargingServer(msg.sender) || msg.sender == owner, "Apenas um Dos Servidores de Carregamento ou Administrador Pode Executar Esta Acao!");
        _;
    }

    // Construtor:
    constructor(address _authorizedServersAddress) {
        owner = msg.sender; // Define o Deployer do Contrato Como o Owner.
        authorizedServers = AuthorizedServers(_authorizedServersAddress);
        nextReservationID = 1;
    }

    // Criando uma Nova Reserva:
    function createReservation(
        uint256 _chargingStationID,
        uint256 _chargingPointID,
        string memory _cityCodename,
        string memory _companyName,
        uint256 _chargingPointPower,
        uint256 _kWhPrice,
        uint256 _startTimestamp,
        uint256 _finishTimestamp,
        uint256 _price,
        address _customerAddress // Endereço da Carteira do Cliente.
    ) public onlyServerOrOwner {
        // Criando a Reserva:
        uint256 newReservationID = nextReservationID;
        reservations[newReservationID] = Reservation({
            reservationID: newReservationID,
            chargingStationID: _chargingStationID,
            chargingPointID: _chargingPointID,
            cityCodename: _cityCodename,
            companyName: _companyName,
            chargingPointPower: _chargingPointPower,
            kWhPrice: _kWhPrice,
            startTimestamp: _startTimestamp,
            finishTimestamp: _finishTimestamp,
            price: _price,
            customer: payable(_customerAddress),
            status: Status.PENDING
        });

        // Associando o ID da Reserva ao Endereço da Carteira do Cliente:
        customerReservationIDs[_customerAddress].push(newReservationID);

        // Incrementando o ID Para a Próxima Reserva:
        nextReservationID++;

        // Emitindo a Notificação:
        emit ReservationCreated(
            newReservationID,
            _customerAddress,
            _cityCodename,
            _price
        );
    }

    // Confirmando uma Reserva:
    function confirmReservation(uint256 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Nao e Possivel Confirmar uma Reserva Cancelada!");
        require(reservations[_reservationID].status == Status.PENDING, "Nao e Possivel Confirmar uma Reserva Ja Confirmada ou Finalizada!");
        
        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.CONFIRMED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Marcando uma Reserva Como Paga:
    // A Função Será Usada Após a Gravação de Um Transação.
    function markReservationAsPayed(uint256 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Nao e Possivel Marcar uma Reserva Cancelada Como Paga!");
        require(reservations[_reservationID].status == Status.CONFIRMED, "Nao e Possivel Marcar uma Reserva Pendente de Confirmacao Como Paga");
        
        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.PAYED;
        
        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Cancelando uma Reserva Existente:
    function cancelReservation(uint256 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Nao e Possivel Cancelar uma Reserva Ja Cancelada!");
        require(reservations[_reservationID].status != Status.PAYED, "Nao e Possivel Cancelar uma Reserva Paga!");
        require(block.timestamp < reservations[_reservationID].startTimestamp, "Nao e Possivel Cancelar uma Reserva Ja Iniciada!");

        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.CANCELLED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Função para Auditar uma Reserva:
    function getReservation(uint256 _reservationID) public view returns (Reservation memory) {
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        return reservations[_reservationID];
    }

    // Função para Retornar Auditar as Reservas de um Cliente:
    function getReservationsByCustomer(address _customerAddress) public view returns (Reservation[] memory){
        // Verificando o Endereço:
        require(_customerAddress != address(0), "Endereco do Usuario Invalido!");
        
        // Obtendo Todas os IDs de Reserva Associadas a Este Cliente:
        uint256[] storage customerIDs = customerReservationIDs[_customerAddress];
        
        // Criando um Array em Memória para Armazenar as Structs de Reserva Completas:
        Reservation[] memory customerResList = new Reservation[](customerIDs.length);

        // Iterando Sobre as IDs e Preenchendo o Array de Structs:
        for (uint i = 0; i < customerIDs.length; i++) {
            customerResList[i] = reservations[customerIDs[i]];
        }

        return customerResList;
    }

    // Auditando Todas as Reservas do Contrato:
    function getAllReservations() public view returns (Reservation[] memory) {
        Reservation[] memory allResList = new Reservation[](nextReservationID - 1);
        for (uint256 i = 1; i < nextReservationID; i++) {
            allResList[i - 1] = reservations[i];
        }
        return allResList;
    }
}
