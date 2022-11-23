# avoid " unresolved reference" from Room
# import

from typing import Optional,Union


class PeerAppData:
    def __init__(self, displayName: str, device: dict, rtpCapabilities: dict = None,
                 sctpCapabilities: dict = None,
                 transports: list = None,
                 producers: list = None, consumers: list = None, dataProducers: list = None,
                 dataConsumers: list = None):
        self._displayName = displayName
        self._device = device
        self._rtpCapabilities = rtpCapabilities
        self._sctpCapabilities = sctpCapabilities
        self._transports = transports
        self._producers = producers
        self._consumers = consumers
        self._dataProducers = dataProducers
        self._dataConsumers = dataConsumers

    @property
    def displayName(self) -> str:
        return self._displayName

    @displayName.setter
    def displayName(self, displayName):
        self._displayName = displayName

    @property
    def device(self) -> dict:
        return self._device

    @property
    def rtpCapabilities(self) -> dict:
        return self._rtpCapabilities

    @property
    def sctpCapabilities(self) -> dict:
        return self._sctpCapabilities

    @property
    def transports(self) -> list:
        return self._transports

    @property
    def producers(self) -> list:
        return self._producers

    @property
    def consumers(self) -> list:
        return self._consumers

    @property
    def dataProducers(self) -> list:
        return self._dataProducers

    @property
    def dataConsumers(self) -> list:
        return self._dataConsumers

    def __str__(self):
        return 'PeerAppData(' \
               + 'displayName=' + self._displayName \
               + ', device=' + str(self._device) \
               + ', rtpCapabilities=' + str(self._rtpCapabilities) \
               + ', sctpCapabilities=' + str(self._sctpCapabilities) \
               + ', transports=' + str(self._transports) \
               + ', producers=' + str(self._producers) \
               + ', consumers=' + str(self._consumers) \
               + ', dataProducers=' + str(self._dataProducers) \
               + ', dataConsumers=' + str(self._dataConsumers) \
               + ')'


class Peer:
    # todo room: Room
    def __init__(self, room, peerId: str = None, data: PeerAppData = None):
        self._peerId = peerId
        self._room = room
        self._data = data

    @property
    def peerId(self) -> str:
        return self._peerId

    @peerId.setter
    def peerId(self, peerId):
        self._peerId = peerId

    @property
    # todo room: -> Room
    def room(self):
        return self._room

    @property
    def data(self) -> PeerAppData:
        return self._data

    @data.setter
    def data(self, data: PeerAppData):
        self._data = data

    def __str__(self):
        return 'Peer(' \
               + 'peerId=' + self._peerId \
               + ', roomId=' + self._room.roomId \
               + ', data=' + str(self._data) \
               + ')'


class Room:
    def __init__(self, serverAddress: str = None, roomId: str = None):
        self._serverAddress = serverAddress
        self._roomId = roomId
        # <peerId, Peer>
        self._peerIdToPeerMap = {}
        # <producerId, Peer>
        # const { peerId } = producer.appData;
        self._producerIdToPeerMap = {}
        # <consumerId, Peer>
        # const { peerId } = consumer.appData;
        self._consumerIdToPeerMap = {}
        # <dataConsumerId, Peer>
        self._dataConsumerIdToPeerMap = {}

    @property
    def serverAddress(self) -> str:
        return self._serverAddress

    @serverAddress.setter
    def serverAddress(self, serverAddress):
        self._serverAddress = serverAddress

    @property
    def roomId(self) -> str:
        return self._roomId

    @roomId.setter
    def roomId(self, roomId):
        self._roomId = roomId

    def getPeerByProducerId(self, producerId: str) -> Peer:
        return self._producerIdToPeerMap[producerId]

    def getPeerByConsumerId(self, consumerId: str) -> Peer:
        return self._consumerIdToPeerMap[consumerId]

    def bindConsumerIdToPeer(self, consumerId: str, peer: Peer):
        self._consumerIdToPeerMap[consumerId] = peer

    def unbindConsumerIdToPeer(self, consumerId: str, peer: Peer):
        del self._consumerIdToPeerMap[consumerId]

    def getPeerByDataConsumerId(self, dataConsumerId: str) -> Peer:
        return self._dataConsumerIdToPeerMap[dataConsumerId]

    def bindDataConsumerIdToPeer(self, consumerId: str, peer: Peer):
        self._dataConsumerIdToPeerMap[consumerId] = peer

    def unbindDataConsumerIdToPeer(self, consumerId: str, peer: Peer):
        del self._dataConsumerIdToPeerMap[consumerId]

    def getPeerByPeerId(self, peerId: str) -> Optional[Peer]:
        if self._peerIdToPeerMap.get(peerId):
            return self._peerIdToPeerMap[peerId]
        else:
            return None

    def addPeer(self, peerId: str, data: Union[PeerAppData, Peer]) -> Peer:
        if isinstance(data, PeerAppData):
            newPeer = Peer(room=self, peerId=peerId, data=data)
        else:
            newPeer = data
        self._peerIdToPeerMap[peerId] = newPeer
        return newPeer

    def removePeer(self, peerId: str):
        toRemovePeer = self._peerIdToPeerMap[peerId]
        del self._peerIdToPeerMap[peerId]
        return toRemovePeer

    def __str__(self):
        return 'Room(' \
               + 'serverAddress=' + self._serverAddress \
               + ', roomId=' + self._roomId \
               + ', peerIdToPeerMap=' + str(self._peerIdToPeerMap) \
               + ', producerIdToPeerMap=' + str(self._producerIdToPeerMap) \
               + ', consumerIdToPeerMap=' + str(self._consumerIdToPeerMap) \
               + ', dataConsumerIdToPeerMap=' + str(self._dataConsumerIdToPeerMap) \
               + ')'
