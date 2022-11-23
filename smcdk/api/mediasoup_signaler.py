import asyncio
import json
# for ProtooSignaler
import random
import ssl
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Dict

import websockets


class MediasoupSignalerInterface(metaclass=ABCMeta):

    @abstractmethod
    async def connectToRoom(self, loop, serverAddress, roomId, peerId, enableSslVerification: bool = True):
        pass

    @abstractmethod
    async def getRouterRtpCapabilities(self) -> int:
        pass

    @abstractmethod
    async def createSendTransport(self, sctpCapabilities: dict):
        pass

    @abstractmethod
    async def createRecvTransport(self, sctpCapabilities: dict):
        pass

    @abstractmethod
    async def join(self, displayName: str, device: dict, rtpCapabilities: dict, sctpCapabilities: dict):
        pass

    @abstractmethod
    async def connectWebRtcTransport(self, transportId: str, dtlsParameters: dict):
        pass

    @abstractmethod
    async def produce(self, transportId: str, kind: str, rtpParameters: dict, appData: dict):
        pass

    @abstractmethod
    async def produceData(self, transportId: str, label: str, protocol: str, sctpStreamParameters: dict, appData: dict):
        pass

    @abstractmethod
    async def receiveMessage(self):
        pass

    @abstractmethod
    async def responseToNewConsumer(self, requestId: int):
        pass

    @abstractmethod
    async def responseToNewDataConsumer(self, requestId: int):
        pass

    @abstractmethod
    def setResponse(self, message: dict):
        pass

    @abstractmethod
    async def getResponse(self, requestId: int):
        pass


class ProtooSignaler(MediasoupSignalerInterface):

    def __init__(self):
        self._loop = None
        self._ctx = None
        self._websocket = None
        self._roomUri = None
        self._responses: Dict[int, asyncio.Future] = {}

    async def connectToRoom(self, loop: asyncio.AbstractEventLoop, serverAddress, roomId,
                            peerId, enableSslVerification: bool = True):  # todo: 格式化，并存储roomId
        self._loop = loop
        self._roomUri = f'wss://{serverAddress}/?roomId={roomId}&peerId={peerId}'
        self._ctx = ssl.create_default_context()
        if not enableSslVerification:
            self._ctx.check_hostname = False
            self._ctx.verify_mode = ssl.CERT_NONE
        self._websocket = await websockets.connect(self._roomUri, subprotocols=['protoo'], ssl=self._ctx)

    async def closeCurrentConnection(self):
        self._websocket.close()
        self._loop = None

    @staticmethod
    def generateRandomNumber() -> int:
        return round(random.random() * 10000000)

    async def getRouterRtpCapabilities(self) -> int:
        return await self._send_request({
            'request': True,
            'method': 'getRouterRtpCapabilities',
            'data': {}
        })

    async def createSendTransport(self, sctpCapabilities: dict):
        return await self._send_request({
            'request': True,
            'method': 'createWebRtcTransport',
            'data': {
                'forceTcp': False,
                'producing': True,
                'consuming': False,
                'sctpCapabilities': sctpCapabilities
            }
        })

    async def createRecvTransport(self, sctpCapabilities: dict):
        return await self._send_request({
            'request': True,
            'method': 'createWebRtcTransport',
            'data': {
                'forceTcp': False,
                'producing': False,
                'consuming': True,
                'sctpCapabilities': sctpCapabilities
            }
        })

    async def join(self, displayName: str, device: dict, rtpCapabilities: dict, sctpCapabilities: dict):
        return await self._send_request({
            'request': True,
            'method': 'join',
            'data': {
                "displayName": displayName,
                'device': device,
                "rtpCapabilities": rtpCapabilities,
                "sctpCapabilities": sctpCapabilities
            }
        })

    async def connectWebRtcTransport(self, transportId: str, dtlsParameters: dict):
        return await self._send_request({
            "request": True,
            "method": "connectWebRtcTransport",
            "data": {
                "transportId": transportId,
                "dtlsParameters": dtlsParameters
            }
        })

    async def produce(self, transportId: str, kind: str, rtpParameters: dict, appData: dict):
        return await self._send_request({
            'method': 'produce',
            'request': True,
            'data': {
                'transportId': transportId,
                'kind': kind,
                'rtpParameters': rtpParameters,
                'appData': appData
            }
        })

    async def produceData(self, transportId: str, label: str, protocol: str, sctpStreamParameters: dict, appData: dict):
        return await self._send_request({
            'method': 'produceData',
            'request': True,
            'data': {
                'transportId': transportId,
                'label': label,
                'protocol': protocol,
                'sctpStreamParameters': sctpStreamParameters,
                'appData': appData
            }
        })

    async def _send_request(self, requestParameters: dict) -> int:
        requestParameters['id'] = ProtooSignaler.generateRandomNumber()
        self._responses[requestParameters['id']] = self._loop.create_future()
        await self._websocket.send(json.dumps(requestParameters))
        return requestParameters['id']

    async def _send_response(self, responseParameters: dict):
        await self._websocket.send(json.dumps(responseParameters))

    async def receiveMessage(self):
        return json.loads(await self._websocket.recv())

    async def responseToNewConsumer(self, requestId: str):
        return await self._send_response({
            'response': True,
            'id': requestId,
            'ok': True,
            'data': {}
        })

    async def responseToNewDataConsumer(self, requestId: str):
        return await self._send_response({
            'response': True,
            'id': requestId,
            'ok': True,
            'data': {}
        })

    def setResponse(self, message: dict):
        self._responses[message['id']].set_result(message)

    async def getResponse(self, requestId: int):
        # print(f'getResponse: {requestId}')
        try:
            message = await asyncio.wait_for(fut=self._responses[requestId], timeout=10)
            return Response(requestId=message['id'], method=None, data=message['data'])
        except asyncio.TimeoutError:
            raise Exception("operation timed out")


class MessageType(Enum):
    CLIENT_REQUEST_getRouterRtpCapabilities = 'getRouterRtpCapabilities'
    SERVER_REQURST_newPeer = 'newPeer'
    SERVER_REQURST_newConsumer = 'newConsumer'
    SERVER_REQURST_newDataConsumer = 'newDataConsumer'
    # bandwidth
    SERVER_NOTIFICATION_downlinkBwe = 'downlinkBwe'
    # peer
    SERVER_NOTIFICATION_activeSpeaker = 'activeSpeaker'
    SERVER_NOTIFICATION_newPeer = 'newPeer'
    SERVER_NOTIFICATION_peerDisplayNameChanged = 'peerDisplayNameChanged'
    SERVER_NOTIFICATION_peerClosed = 'peerClosed'
    # producer
    SERVER_NOTIFICATION_producerScore = 'producerScore'
    # consumer
    SERVER_NOTIFICATION_consumerScore = 'consumerScore'
    SERVER_NOTIFICATION_consumerLayersChanged = 'consumerLayersChanged'
    SERVER_NOTIFICATION_consumerPaused = 'consumerPaused'
    SERVER_NOTIFICATION_consumerResumed = 'consumerResumed'
    SERVER_NOTIFICATION_consumerClosed = 'consumerClosed'
    # dataConsumer
    SERVER_NOTIFICATION_dataConsumerClosed = 'dataConsumerClosed'


class SignalerMessage:
    def __init__(self, requestId: int, method: str, data: dict):
        self._requestId = requestId
        self._method = method
        self._data = data

    @property
    def requestId(self) -> int:
        return self._requestId

    @property
    def method(self) -> str:
        return self._method

    @property
    def data(self) -> dict:
        return self._data


class Request(SignalerMessage):
    def __str__(self):
        return 'Request(' \
               + 'requestId=' + str(self._requestId) \
               + ', method=' + self._method \
               + ', data=' + str(self._data) \
               + ')'


class Response(SignalerMessage):
    def __str__(self):
        return 'Response(' \
               + 'requestId=' + str(self._requestId) \
               + ', data=' + str(self._data) \
               + ')'


class Notification(SignalerMessage):
    def __str__(self):
        return 'Notification(' \
               + 'method=' + self._method \
               + ', data=' + str(self._data) \
               + ')'
