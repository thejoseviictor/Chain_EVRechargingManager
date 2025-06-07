pragma solidity ^0.8.0;

contract Reservation {
    struct ReservationInfos {

        address cliente;

        string reservationID;
        string chargingStationID;
        string chargingPointID;
        string chargingPointPower;
        string kWhPrice;
        string vehicleID;
        string origem;
        string destino;
        uint timestamp;
    }