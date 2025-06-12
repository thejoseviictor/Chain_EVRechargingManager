// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Importando as Dependências dos Outros Contratos:
import "./AuthorizedServers.sol";
import "./ReservationLedger.sol";

contract Escrow {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Referência aos Contratos "AuthorizedServers" e "ReservationLedger":
    AuthorizedServers public authorizedServers;
    ReservationLedger public reservationLedger;

    // Dados do Pagamento:
    struct EscrowPayment {
        address payable payer; // Cliente (Carteira do Carro).
        address payable recipient; // Servidor (Carteira do Servidor).
        uint256 amount; // Valor em "wei".
        bool paidToEscrow; // Se o Valor Foi Depositado no Escrow.
        bool released; // Se o Valor Foi Liberado Para o Recebedor.
    }

    // Mapeamento:
    mapping(uint256 => EscrowPayment) public escrowPayments;

    // Eventos para Notificações:
    event FundsDeposited(uint256 indexed reservationID, address indexed payer, uint256 amount); // Pagamento Depositado.
    event FundsReleased(uint256 indexed reservationID, address indexed recipient, uint256 amount); // Pagamento Liberado.
    event EscrowInitialized(uint256 indexed reservationID, address payer, address recipient, uint256 amount);

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
    constructor(address _authorizedServersAddress, address _reservationLedgerAddress) {
        owner = msg.sender; // Define o Deployer do Contrato Como o Owner.
        authorizedServers = AuthorizedServers(_authorizedServersAddress);
        reservationLedger = ReservationLedger(_reservationLedgerAddress);
    }

    // Iniciando o Processo de Escrow Para uma Reserva Específica:
    function initializeEscrow(
        uint256 _reservationID,
        address payable _payer,
        address payable _recipient,
        uint256 _amount
    ) public onlyServerOrOwner {
        // Verificando o Status da Reserva:
        require(reservationLedger.getReservation(_reservationID).status == ReservationLedger.Status.CONFIRMED, "Reserva Nao Confirmada no 'ReservationLedger'!");

        // Verificando as Informações dos Parâmetros do Escrow:
        // "address(0)" é Um Valor Padrão, Quando os Valores da Struct Ainda Não Foi Inicializados:
        require(escrowPayments[_reservationID].payer == address(0), "Escrow Ja Inicializado Para Esta Reserva!");
        require(_payer != address(0), "Endereco do Pagador Invalido!");
        require(_recipient != address(0), "Endereco do Recebedor Invalido!");
        require(_amount > 0, "O Valor Deve Ser Maior Que Zero!");

        // Criando o Escrow:
        escrowPayments[_reservationID] = EscrowPayment({
            payer: _payer,
            recipient: _recipient,
            amount: _amount,
            paidToEscrow: false,
            released: false
        });

        // Emitindo a Notificação:
        emit EscrowInitialized(_reservationID, _payer, _recipient, _amount);
    }

    // Depositando o Valor da Recarga no Contrato de Escrow, Através do Veículo:
    function depositFunds(uint256 _reservationID) public payable {
        EscrowPayment storage payment = escrowPayments[_reservationID];

        // Verificando as Informações do Escrow:
        require(payment.payer != address(0), "Escrow Nao Inicializado Para Esta Reserva!");
        require(!payment.paidToEscrow, "Fundos Ja Depositados!");
        require(msg.value == payment.amount, "Valor Enviado Nao Corresponde ao Valor da Reserva!");

        // Atualizando o Status de Pagamento:
        payment.paidToEscrow = true;

        // Emitindo a Notificação:
        emit FundsDeposited(_reservationID, msg.sender, msg.value);
    }

    // Liberando os Fundos do Escrow Para o Servidor de Recarga:
    // Apenas o Administrador Pode Fazer Isso:
    function releaseFunds(uint256 _reservationID) public onlyOwner {
        EscrowPayment storage payment = escrowPayments[_reservationID];

        // Verificando as Informações do Escrow:
        require(payment.paidToEscrow, "Fundos Nao Depositados no Escrow!");
        require(!payment.released, "Fundos Ja Liberados!");
        
        // Verificando o Status da Reserva:
        require(reservationLedger.getReservation(_reservationID).status == ReservationLedger.Status.PAYED, "Reserva Nao Marcada Como Paga no 'ReservationLedger'!");

        // Transferindo o Valor Para o Recebedor (Servidor):
        (bool success, ) = payment.recipient.call{value: payment.amount}("");
        require(success, "Falha ao Liberar Fundos!");

        // Atualizando o Status de Liberação do Pagamento:
        payment.released = true;

        // Emitindo a Notificação:
        emit FundsReleased(_reservationID, payment.recipient, payment.amount);
    }

    // Retornando o Status de Um Pagamento de Escrow:
    function getEscrowPaymentStatus(uint256 _reservationID) public view returns (EscrowPayment memory) {
        require(escrowPayments[_reservationID].payer != address(0), "Pagamento de Escrow Invalido ou Nao Encontrado!");
        return escrowPayments[_reservationID];
    }
}
