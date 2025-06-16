// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

// Importando as Dependências dos Outros Contratos:
import "./AuthorizedServers.sol";
import "./ReservationLedger.sol";
import "./TransactionLedger.sol";
import "./Escrow.sol";

contract ChargingSessionManager {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Referência aos Contratos "AuthorizedServers", "ReservationLedger" e "Escrow":
    AuthorizedServers public authorizedServers;
    ReservationLedger public reservationLedger;
    TransactionLedger public transactionLedger;
    Escrow public escrow;

    // Status da Sessão de Recarga:
    enum SessionStatus {IDLE, IN_PROGRESS, FINISHED}

    // Dados da Sessão de Recarga:
    struct ChargingSession {
        uint256 reservationID;
        address customer;
        SessionStatus status;
    }

    // Mapeamento:
    mapping(uint256 => ChargingSession) public chargingSessions;

    // Evento para Notificação:
    event SessionStatusUpdated(uint256 indexed reservationID, SessionStatus status);

    // Modificadores:
    modifier onlyOwner() {
        require(msg.sender == owner, "Apenas o Administrador Pode Executar Esta Acao!");
        _;
    }
    modifier onlyServerOrOwner() {
        require(authorizedServers.isAuthorizedRechargingServer(msg.sender) || msg.sender == owner, "Apenas um Dos Servidores de Carregamento ou Administrador Pode Executar Esta Acao!");
        _;
    }

    // Construtor:
    constructor(address _authorizedServersAddress, address _reservationLedgerAddress, address _transactionLedger, address _escrowAddress) {
        owner = msg.sender;
        authorizedServers = AuthorizedServers(_authorizedServersAddress);
        reservationLedger = ReservationLedger(_reservationLedgerAddress);
        transactionLedger = TransactionLedger(_transactionLedger);
        escrow = Escrow(_escrowAddress);
    }

    // Iniciando uma Sessão de Recarga Para Uma Reserva Confirmada:
    function startChargingSession(
        uint256 _reservationID
    ) public onlyServerOrOwner {
        // Verificando as Informações da Reserva:
        require(reservationLedger.getReservation(_reservationID).reservationID != 0, "ID da Reserva Invalido!");
        require(reservationLedger.getReservation(_reservationID).status == ReservationLedger.Status.CONFIRMED, "A Reserva Nao Esta Confirmada!");

        // Verificando o Depósito dos Fundos no Escrow:
        require(escrow.getEscrowPaymentStatus(_reservationID).paidToEscrow, "Os Fundos Nao Foram Depositados Para Esta Reserva!");
        
        // Verificando as Informações da Sessão de Recarga da Reserva:
        require(chargingSessions[_reservationID].reservationID == 0, "Sessao de Recarga Ja Iniciada Para Esta Reserva!");

        // Criando a Nova Sessão de Recarga:
        chargingSessions[_reservationID] = ChargingSession({
            reservationID: _reservationID,
            customer: reservationLedger.getReservation(_reservationID).customer,
            status: SessionStatus.IN_PROGRESS
        });

        // Emitindo uma Notificação:
        emit SessionStatusUpdated(chargingSessions[_reservationID].reservationID, SessionStatus.IN_PROGRESS);
    }

    // Finalizando uma Sessão de Recarga e Liberando o Fundos de Pagamento:
    function finishChargingSession(
        uint256 _reservationID
    ) public onlyOwner {
        // Verificando as Informações da Recarga:
        ChargingSession storage session = chargingSessions[_reservationID];
        require(session.reservationID != 0, "Sessao de Recarga Nao Encontrada Para Esta Reserva!");
        require(session.status == SessionStatus.IN_PROGRESS, "A Sessao Nao Esta Em Andamento!");

        // Atualizando o Status da Sessão de Recarga:
        session.status = SessionStatus.FINISHED;

        // Registrando a Transação da Reserva no "ReservationLedger":
        transactionLedger.recordTransaction(
            _reservationID,
            escrow.getEscrowPaymentStatus(_reservationID).payer, // Endereço da Carteira do Cliente.
            true // Status de Pagamento.
        );

        // Liberando os Fundos de Pagamento Para o Servidor:
        escrow.releaseFunds(_reservationID);

        // Emitindo uma Notificação:
        emit SessionStatusUpdated(session.reservationID, SessionStatus.FINISHED);
    }

    // Auditando os Detalhes de Uma Sessão de Recarga:
    function getChargingSession(uint256 _reservationID) public view returns (ChargingSession memory) {
        require(chargingSessions[_reservationID].reservationID != 0, "Sessao de Recarga Nao Encontrada!");
        return chargingSessions[_reservationID];
    }
}
