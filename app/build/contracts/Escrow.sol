// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

// Importando as Dependências dos Outros Contratos:
import "./AuthorizedServers.sol";
import "./ReservationLedger.sol";
import "./ChargingSessionManager.sol";

contract Escrow {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Referência aos Contratos "AuthorizedServers", "ReservationLedger" e "ChargingSessionManager":
    AuthorizedServers public authorizedServers;
    ReservationLedger public reservationLedger;
    ChargingSessionManager public chargingSessionManager;

    // Dados do Pagamento:
    struct EscrowPayment {
        address payable payer; // Cliente (Carteira do Carro).
        address payable recipient; // Servidor (Carteira do Servidor).
        uint72 amount; // Valor em "wei", Até "100" ETH em "wei" (1e20).
        bool paidToEscrow; // Se o Valor Foi Depositado no Escrow.
        bool released; // Se o Valor Foi Liberado Para o Recebedor.
        uint32 paymentTimestamp;
    }

    // Mapeamento:
    mapping(uint16 => EscrowPayment) public escrowPayments; // Até 65536 Escrows de Pagamento Possíveis.

    // Eventos para Notificações:
    event FundsDeposited(uint16 indexed reservationID, address indexed payer, uint72 amount); // Pagamento Depositado.
    event FundsReleased(uint16 indexed reservationID, address indexed recipient, uint72 amount); // Pagamento Liberado.
    event EscrowInitialized(uint16 indexed reservationID, address payer, address recipient, uint72 amount);

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
    constructor(address _authorizedServersAddress, address _reservationLedgerAddress, address _chargingSessionManagerAddress) {
        owner = msg.sender; // Define o Deployer do Contrato Como o Owner.
        authorizedServers = AuthorizedServers(_authorizedServersAddress);
        reservationLedger = ReservationLedger(_reservationLedgerAddress);
        chargingSessionManager = ChargingSessionManager(_chargingSessionManagerAddress);
    }

    // Iniciando o Processo de Escrow Para uma Reserva Específica:
    function initializeEscrow(uint16 _reservationID) public onlyServerOrOwner {
        // Recuperando os Dados da Reserva:
        ReservationLedger.Reservation memory rs = reservationLedger.getReservation(_reservationID);
        
        // Verificando o Status da Reserva:
        require(rs.status == ReservationLedger.Status.CONFIRMED, "Reserva Nao Confirmada no 'ReservationLedger'!");

        // Verificando as Informações dos Parâmetros do Escrow:
        // "address(0)" é Um Valor Padrão, Quando os Valores da Struct Ainda Não Foi Inicializados:
        require(escrowPayments[_reservationID].payer == address(0), "Escrow Ja Inicializado Para Esta Reserva!");

        // Criando o Escrow:
        escrowPayments[_reservationID] = EscrowPayment({
            payer: rs.customer,
            recipient: rs.recipient,
            amount: rs.price,
            paidToEscrow: false,
            released: false,
            paymentTimestamp: uint32(block.timestamp)
        });

        // Emitindo a Notificação:
        emit EscrowInitialized(_reservationID, rs.customer, rs.recipient, rs.price);
    }

    // Depositando o Valor da Recarga no Contrato de Escrow, Através do Veículo:
    function depositFunds(uint16 _reservationID) public payable {
        EscrowPayment storage payment = escrowPayments[_reservationID];

        // Verificando as Informações do Escrow:
        require(payment.payer != address(0), "Escrow Nao Inicializado Para Esta Reserva!");
        require(!payment.paidToEscrow, "Fundos Ja Depositados!");
        require(msg.value == payment.amount, "Valor Enviado Nao Corresponde ao Valor da Reserva!");

        // Atualizando o Pagador, Caso Não Seja o Cliente:
        payment.payer = payable(msg.sender);

        // Atualizando o Status de Pagamento e Horário do Pagamento:
        payment.paidToEscrow = true;
        payment.paymentTimestamp = uint32(block.timestamp);

        // Marcando a Reserva Como Paga:
        reservationLedger.markReservationAsPaid(_reservationID);

        // Emitindo a Notificação:
        emit FundsDeposited(_reservationID, msg.sender, uint72(msg.value));
    }

    // Liberando os Fundos do Escrow Para o Servidor de Recarga:
    // Apenas o Administrador Pode Fazer Isso:
    function releaseFunds(uint16 _reservationID) public onlyOwner {
        EscrowPayment storage payment = escrowPayments[_reservationID];

        // Recuperando os Dados da Sessão de Carregamento:
        ChargingSessionManager.ChargingSession memory cs = chargingSessionManager.getChargingSession(_reservationID);

        // Verificando as Informações do Escrow e Sessão de Carregamento:
        require(payment.paidToEscrow, "Fundos Nao Depositados no Escrow!");
        require(!payment.released, "Fundos Ja Liberados!");
        require(cs.status == ChargingSessionManager.SessionStatus.FINISHED, "Nao Foi Possivel Liberar os Fundos, Pois a Sessao de Carregamento Nao Foi Finalizada!");

        // Transferindo o Valor Para o Recebedor (Servidor):
        (bool success, ) = payment.recipient.call{value: payment.amount}("");
        require(success, "Falha ao Liberar Fundos!");

        // Atualizando o Status de Liberação do Pagamento:
        payment.released = true;

        // Emitindo a Notificação:
        emit FundsReleased(_reservationID, payment.recipient, payment.amount);
    }

    // Retornando o Status de Um Pagamento de Escrow:
    function getEscrowPaymentStatus(uint16 _reservationID) public view returns (EscrowPayment memory) {
        require(escrowPayments[_reservationID].payer != address(0), "Pagamento de Escrow Invalido ou Nao Encontrado!");
        return escrowPayments[_reservationID];
    }
}
