import os
from typing import Union, Optional, Literal

from aiortc import VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaBlackhole, MediaRecorder
from aiortc.mediastreams import AudioStreamTrack

from smcdk import Device, AiortcHandler
from smcdk.consumer import Consumer
from smcdk.data_consumer import DataConsumer
from smcdk.producer import Producer
from smcdk.rtp_parameters import RtpCapabilities
from smcdk.sctp_parameters import SctpCapabilities, SctpStreamParameters
from smcdk.transport import Transport
from .room_peer import Peer


class MultimediaRuntime:
    def __init__(self):
        # original mediasoup device
        self._device: Device = None
        '''
        sendTransport and its producers part
        '''
        self._sendTransport: Transport = None
        self._producers: list = []
        self._autoProduce: bool = True
        self._canProduce: bool = False
        self._player: MediaPlayer = None
        self._mediaFilePath: str = None
        self._videoTrack: VideoStreamTrack = None
        self._audioTrack: AudioStreamTrack = None
        self._tracks: list = []
        '''
        recvTransport and its consumers(include dataConsumers) part
        '''
        self._recvTransport: Transport = None
        self._dataConsumers: list = []
        self._consumers: list = []
        self._autoConsume: bool = True
        self._canConsume: bool = True
        self._recordDirectoryPath = None
        # self._recordFilePathGenerator:function
        self._recorders: dict = {}

    @property
    def autoProduce(self) -> bool:
        return self._autoProduce

    @property
    def canProduce(self) -> bool:
        return self._canProduce

    @property
    def autoConsume(self) -> bool:
        return self._autoConsume

    @property
    def canConsume(self) -> bool:
        return self._canConsume

    def initializeProducerAndConsumerOptions(self, autoProduce: bool, mediaFilePath: str, autoConsume: bool,
                                             recordDirectoryPath: str, recordFilePathGenerator):
        """"""
        '''
        producer part
        '''
        self._autoProduce = autoProduce
        self._mediaFilePath = mediaFilePath
        self._canProduce = self._mediaFilePath is not None
        '''        
        consumer part 
        '''
        self._autoConsume = autoConsume
        self._recordDirectoryPath = recordDirectoryPath
        # if recordFilePathGenerator:
        #     self._recordFilePathGenerator = recordFilePathGenerator
        # else:
        #     self._recordFilePathGenerator = self._generateRecordFilePath
        self._canConsume = self._recordDirectoryPath is not None

    def _preparePlayerEngine(self):
        if self._mediaFilePath != '':
            self._player = MediaPlayer(self._mediaFilePath)
        if self._player and self._player.video:
            self._videoTrack = self._player.video
        elif self._mediaFilePath == '':
            self._videoTrack = VideoStreamTrack()
        self._tracks.append(self._videoTrack)
        if self._player and self._player.audio:
            self._audioTrack = self._player.audio
        elif self._mediaFilePath == '':
            self._audioTrack = AudioStreamTrack()
        self._tracks.append(self._audioTrack)

    async def loadDevice(self, routerRtpCapabilities: Union[RtpCapabilities, dict]):
        if len(self._tracks) == 0:
            self._preparePlayerEngine()
        self._device = Device(handlerFactory=AiortcHandler.createFactory(tracks=self._tracks))
        await self._device.load(routerRtpCapabilities)
        self._canProduce &= self._device.canProduce('audio') or self._device.canProduce('video')
        # MediaBlackhole is always able to consume
        # self._canConsume = True

    @property
    def rtpCapabilities(self) -> Optional[RtpCapabilities]:
        if self._device:
            return self._device.rtpCapabilities
        else:
            raise Exception('device has not loaded')

    @property
    def sctpCapabilities(self) -> Optional[SctpCapabilities]:
        if self._device:
            return self._device.sctpCapabilities
        else:
            raise Exception('device has not loaded')

    def createSendTransport(self, transportId: str, iceParameters, iceCandidates, dtlsParameters, sctpParameters,
                            onConnectFunc, onProduceFunc, onProduceDataFunc):
        self._sendTransport = self._device.createSendTransport(
            id=transportId,
            iceParameters=iceParameters,
            iceCandidates=iceCandidates,
            dtlsParameters=dtlsParameters,
            sctpParameters=sctpParameters
        )

        @self._sendTransport.on('connect')
        async def onConnect(inputDtlsParameters):
            await onConnectFunc(inputDtlsParameters)

        @self._sendTransport.on('produce')
        async def onProduce(kind: str, rtpParameters, appData: dict):
            return await onProduceFunc(kind, rtpParameters, appData)

        @self._sendTransport.on('producedata')
        async def onProduceData(
                sctpStreamParameters: SctpStreamParameters,
                label: str,
                protocol: str,
                appData: dict
        ):
            return await onProduceDataFunc(sctpStreamParameters, label, protocol, appData)

    @property
    def sendTransportId(self):
        if self._sendTransport:
            return self._sendTransport.id
        else:
            return None

    def createRecvTransport(self, transportId: str, iceParameters, iceCandidates, dtlsParameters, sctpParameters,
                            onConnectFunc):
        self._recvTransport = self._device.createRecvTransport(
            id=transportId,
            iceParameters=iceParameters,
            iceCandidates=iceCandidates,
            dtlsParameters=dtlsParameters,
            sctpParameters=sctpParameters
        )

        @self._recvTransport.on('connect')
        async def onConnect(inputDtlsParameters):
            await onConnectFunc(inputDtlsParameters)

    @property
    def recvTransportId(self):
        if self._recvTransport:
            return self._recvTransport.id
        else:
            return None

    async def produce(self):
        if self._videoTrack:
            videoProducer: Producer = await self._sendTransport.produce(
                track=self._videoTrack,
                stopTracks=False,
                appData={}
            )
            self._producers.append(videoProducer)
        if self._audioTrack:
            audioProducer: Producer = await self._sendTransport.produce(
                track=self._audioTrack,
                stopTracks=False,
                appData={}
            )
            self._producers.append(audioProducer)

    def _generateRecordFilePath(self, mePeer: Peer, consumerId: str, producePeer: Peer, producerId: str,
                                kind: Literal['audio', 'video']) -> tuple:
        peerId = producePeer.peerId
        displayName = producePeer.data.displayName
        roomId = mePeer.room.roomId
        suffix: str
        if kind == 'audio':
            suffix = 'mp3'
        else:  # kind == 'video'
            suffix = 'mp4'
        return roomId, f'{displayName}({peerId})_{kind}({consumerId})', suffix

    async def consume(self, mePeer: Peer, consumerId: str,
                      producePeer: Peer, producerId: str, kind: Literal['audio', 'video'], rtpParameters: dict):
        recorder: Union[MediaBlackhole, MediaRecorder]
        if self._recordDirectoryPath == '':
            recorder = MediaBlackhole()
        else:
            relativeDirectory, fileName, suffix = self._generateRecordFilePath(mePeer, consumerId, producePeer,
                                                                               producerId,
                                                                               kind)
            recordFileParentPath = self._recordDirectoryPath + '/' + relativeDirectory
            if not os.path.exists(recordFileParentPath):
                os.makedirs(recordFileParentPath)
            recordFilePath = recordFileParentPath + '/' + f'{fileName}.{suffix}'
            recorder = MediaRecorder(file=recordFilePath)
        self._recorders[producePeer.peerId] = {consumerId: recorder}

        consumer: Consumer = await self._recvTransport.consume(
            id=consumerId,
            producerId=producerId,
            kind=kind,
            rtpParameters=rtpParameters
        )
        self._consumers.append(consumer)
        recorder.addTrack(consumer.track)
        await recorder.start()

    async def consumeData(self, dataConsumerId, dataProducerId, sctpStreamParameters, label, protocol, appData,
                          onMessageFunc):
        dataConsumer: DataConsumer = await self._recvTransport.consumeData(
            id=dataConsumerId,
            dataProducerId=dataProducerId,
            sctpStreamParameters=sctpStreamParameters,
            label=label,
            protocol=protocol,
            appData=appData
        )
        self._dataConsumers.append(dataConsumer)

        @dataConsumer.on('message')
        def onMessage(recvMessage):
            onMessageFunc(recvMessage)

    async def close(self, stopTaskLoopFunc):
        for consumer in self._consumers:
            await consumer.close()
        for dataConsumer in self._dataConsumers:
            await dataConsumer.close()
        for producer in self._producers:
            await producer.close()

        stopTaskLoopFunc()

        if self._sendTransport:
            await self._sendTransport.close()
        if self._recvTransport:
            await self._recvTransport.close()

        for consumerIdToRecorderEntry in self._recorders.values():
            for recorder in consumerIdToRecorderEntry.values():
                await recorder.stop()

        # no MediaPlayer.stop() api
        # await self._player.stop()
