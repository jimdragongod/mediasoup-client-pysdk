import asyncio
import logging

from smcdk.log import Logger
from smcdk.api.mediasoup_signaler import MediasoupSignalerInterface, ProtooSignaler, MessageType, Request
from smcdk.api.multimedia_runtime import MultimediaRuntime
from smcdk.api.notification_listener import BandwidthNotificationListener, PeerNotificationListener, \
    ProducerNotificationListener, ConsumerNotificationListener, DataConsumerNotificationListener
from smcdk.api.request_listener import ConsumerRequestListener, DataConsumerRequestListener
from smcdk.api.room_peer import Room, Peer, PeerAppData

# logger of module level
logger = Logger.getLogger(enable_console=True, level=logging.WARN, log_file_path=None)


class MediasoupClient:

    def __init__(self,
                 signaler: MediasoupSignalerInterface = None,
                 requestListeners: list = None,
                 notificationListeners: list = None):
        """
        instantiate a MediasoupClient object

        :param signaler:
            pluggable signaler implementation of MediasoupSignalerInterface,
            if not provided, default is protooSignaler
        :param requestListeners:
            request listener list of consumer and dataConsumer level,
            if not provided, default is [ConsumerRequestListener, DataConsumerRequestListener],
            if provided, inherit and overwrite these default request listeners
        :param notificationListeners:
            notification listener list,
            if not provided, default is
                [BandwidthNotificationListener, PeerNotificationListener, ProducerNotificationListener,
                    ConsumerNotificationListener, DataConsumerNotificationListener],
            if provided, inherit and overwrite these default notification listeners
        """
        '''
        multimedia runtime, room and peer part        
        '''
        self._multimediaRuntime: MultimediaRuntime = MultimediaRuntime()
        # room should be initialized to be injected into peer
        self._room: Room = Room()
        # peer should be initialized to be injected into listeners
        self._mePeer: Peer = Peer(room=self._room)
        '''
        signaler part
        '''
        if signaler is None:
            self._signaler: MediasoupSignalerInterface = ProtooSignaler()
        else:
            self._signaler: MediasoupSignalerInterface = signaler
        '''
        loop and tasks part
        '''
        self._loop = None
        self._loopTasks = []
        '''
        request listeners
        '''
        if requestListeners is None:
            self._consumerRequestListener: ConsumerRequestListener = ConsumerRequestListener(self._mePeer)
            self._dataConsumerRequestListener: DataConsumerRequestListener = DataConsumerRequestListener(self._mePeer)
        elif len(list) == 2:
            self._consumerRequestListener: ConsumerRequestListener = requestListeners[0]
            self._consumerRequestListener.mePeer = self._mePeer
            self._dataConsumerRequestListener: DataConsumerRequestListener = requestListeners[1]
            self._dataConsumerRequestListener.mePeer = self._mePeer
        else:
            raise Exception(f"wrong length of requestListenerList: {len(requestListeners)}, expect: 2")
        '''
        notification listeners
        '''
        if notificationListeners is None:
            self._bandwidthNotificationListener: BandwidthNotificationListener = BandwidthNotificationListener(
                self._mePeer)
            self._peerNotificationListener: PeerNotificationListener = PeerNotificationListener(self._mePeer)
            self._producerNotificationListener: ProducerNotificationListener = ProducerNotificationListener(
                self._mePeer)
            self._consumerNotificationListener: ConsumerNotificationListener = ConsumerNotificationListener(
                self._mePeer)
            self._dataConsumerNotificationListener: DataConsumerNotificationListener = DataConsumerNotificationListener(
                self._mePeer)
        elif len(notificationListeners) == 5:
            self._bandwidthNotificationListener: BandwidthNotificationListener = notificationListeners[0]
            self._bandwidthNotificationListener.mePeer = self._mePeer
            self._peerNotificationListener: PeerNotificationListener = notificationListeners[1]
            self._peerNotificationListener.mePeer = self._mePeer
            self._producerNotificationListener: ProducerNotificationListener = notificationListeners[2]
            self._producerNotificationListener.mePeer = self._mePeer
            self._consumerNotificationListener: ConsumerNotificationListener = notificationListeners[3]
            self._consumerNotificationListener.mePeer = self._mePeer
            self._dataConsumerNotificationListener: DataConsumerNotificationListener = notificationListeners[4]
            self._dataConsumerNotificationListener.mePeer = self._mePeer
        else:
            raise Exception(f"wrong length of notificationListeners: {len(notificationListeners)}, expect: 5")
        self._notificationListeners = [self._bandwidthNotificationListener, self._peerNotificationListener,
                                       self._producerNotificationListener, self._consumerNotificationListener,
                                       self._dataConsumerNotificationListener]

    # async def joinSingleRoom(self, roomAddressInfo: dict, peerInfo: dict,
    #                          producerConfig: dict,
    #                          consumerConfig: dict):
    #     try:
    #         await self.joinRoom(roomAddressInfo, peerInfo, producerConfig, consumerConfig)
    #     except (asyncio.CancelledError, KeyboardInterrupt):
    #         await self.close()

    async def joinRoom(self, roomAddressInfo: dict, peerInfo: dict, producerConfig: dict, consumerConfig: dict):
        """
        enter the specified room and auto-produce if needed

        :param roomAddressInfo:
            {
                'serverAddress':
                    str, ip:port, required,
                'enableSslVerification':
                    bool, will be sent to MediasoupSignalerInterface.connectToRoom‘s 'enableSslVerification' argument,
                    to check if ssl verification is needed before establish connection to server,
                    the default value is True, that means ssl verification is needed
                'roomId': 'the room's id, required',
            }
        :param peerInfo:
            {
                'peerId':
                    str, the peer id when current MediasoupClient instance join the room, required
                'displayName':
                    str, the peer id when current MediasoupClient instance join the room, default is 'PySDK Client'
                'device':
                    dict, the device info when current MediasoupClient instance join the room,
                    default is
                        {
                            'flag': 'smcdk,pymediasoup,aiortc,python',
                            'name': 'mediasoup-client-pysdk',
                            'version': '1.x'
                        }
            }
        :param producerConfig:
            {
                'autoProduce': bool, default is True
                'mediaFilePath': str, the full path of media file, required
            }
        :param consumerConfig:
            {
                'autoConsume': bool, default is True
                'recordDirectoryPath': str, the root path of to-record media files, required
            }
        :return: None
        """
        logger.info('peer(id=%s, displayName=%s) join room(id=%s)', peerInfo['peerId'], peerInfo['displayName'],
                    roomAddressInfo['roomId'])

        '''
        stuff room and peer part
        '''
        # not first enter
        if self._room.roomId is not None:
            logger.warn('exit from room(id=%s) before join room(id=%s)', self._room.roomId, roomAddressInfo['roomId'])
            await self.exitRoom(self._room.roomId)
        self._room.serverAddress = roomAddressInfo['serverAddress']
        self._room.roomId = roomAddressInfo['roomId']
        self._mePeer.peerId = peerInfo['peerId']
        self._mePeer.data = PeerAppData(displayName=peerInfo.get('displayName', 'PySDK Client'),
                                        device=peerInfo.get('device', {'flag': 'smcdk,pymediasoup,aiortc,python',
                                                                       'name': 'mediasoup-client-pysdk',
                                                                       'version': '1.x'}))
        '''
        stuff multimedia runtime part
        '''
        self._multimediaRuntime.initializeProducerAndConsumerOptions(
            autoProduce=producerConfig.get('autoProduce', True),
            mediaFilePath=producerConfig.get('mediaFilePath'),
            autoConsume=consumerConfig.get('autoConsume', True),
            recordDirectoryPath=consumerConfig.get(
                'recordDirectoryPath'),
            recordFilePathGenerator=consumerConfig.get('recordFilePathGenerator')
        )
        '''
        create connection to server by signaler
        '''
        self._loop = asyncio.get_running_loop()
        logger.info('connectToRoom, serverAddress=%s, roomId=%s, peerId=%s', self._room.serverAddress,
                    self._room.roomId,
                    self._mePeer.peerId)
        await self._signaler.connectToRoom(self._loop, self._room.serverAddress, self._room.roomId, self._mePeer.peerId,
                                           roomAddressInfo['enableSslVerification'])
        '''
        create loop tasks
        '''
        bandwidthNotificationLoop = self._loop.create_task(
            self._bandwidthNotificationListener.runLoop(asyncio.Queue(loop=self._loop)))
        peerNotificationLoop = self._loop.create_task(
            self._peerNotificationListener.runLoop(asyncio.Queue(loop=self._loop)))
        producerNotificationLoop = self._loop.create_task(
            self._producerNotificationListener.runLoop(asyncio.Queue(loop=self._loop)))
        consumerNotificationLoop = self._loop.create_task(
            self._consumerNotificationListener.runLoop(asyncio.Queue(loop=self._loop)))
        dataConsumerNotificationLoop = self._loop.create_task(
            self._dataConsumerNotificationListener.runLoop(asyncio.Queue(loop=self._loop)))
        severEventLoop = self._loop.create_task(self._serverEventLoop())
        self._loopTasks = [severEventLoop, bandwidthNotificationLoop, peerNotificationLoop, producerNotificationLoop,
                           consumerNotificationLoop, dataConsumerNotificationLoop]
        '''
        load device
        '''
        await self._loadDeviceByRouterRtpCapabilities()
        if not (self._multimediaRuntime.canProduce or self._multimediaRuntime.canConsume):
            return
        '''
        create sendTransport & recvTransport 
        '''
        if self._multimediaRuntime.canProduce:
            await self._createSendTransport()
        if self._multimediaRuntime.canConsume:
            await self._createRecvTransport()
        '''
        formally join
        '''
        await self._joinFormally()
        '''
        produce(push media stream to the server) automatically if needed 
        '''
        if self._multimediaRuntime.autoProduce:
            # self._loop.create_task(self._produce(kind='audio', source='mic'), name='produceTask_audio_mic')
            # self._loop.create_task(self._produce(kind='video', source='webCam'), name='produceTask_video_webCam')
            # self._loop.create_task(self._produce(kind='video', source='screenShare'),
            #                        name='produceTask_video_screenShare')
            self._loop.create_task(self._produce())
        '''
        waiting loop tasks
        '''
        await asyncio.gather(severEventLoop, bandwidthNotificationLoop, peerNotificationLoop, producerNotificationLoop,
                             consumerNotificationLoop, dataConsumerNotificationLoop, return_exceptions=True)

    def play(self):
        if self._loop is not None:
            return self._loop.create_task(self._produce())
        else:
            logger.error(f'can\'t play, missing loop({self._loop})')

    async def exitRoom(self, roomId):
        """
        exit current room, prepare to join another
        :param roomId: current room's id to exit, required
        :return: None
        """

        def stopTaskFunc():
            for task in self._loopTasks:
                task.cancel()
            # quick GC, not needed currently
            # for notificationListeners in self._notificationListeners:
            #     notificationListeners.resetQueue(asyncio.Queue)

        await self._multimediaRuntime.close(stopTaskFunc)
        self._room.serverAddress = None
        self._room.roomId = None
        logger.info('exit room %s finished', roomId)

    async def close(self):
        """
        stop current MediasoupClient forever, for purpose of exiting process/thread only

        :return: None
        """
        if self._room.roomId is not None:
            await self.exitRoom(roomId=self._room.roomId)
        else:
            logger.warn('already closed')

    async def _loadDeviceByRouterRtpCapabilities(self):
        requestId = await self._signaler.getRouterRtpCapabilities()
        logger.info('signal request: getRouterRtpCapabilities, requestId=%s', requestId)
        response = await self._signaler.getResponse(requestId)
        await self._multimediaRuntime.loadDevice(response.data)

    async def _createSendTransport(self):
        if self._multimediaRuntime.sendTransportId is not None:
            logger.warn('the sendTransport has already been created')
            return
        requestId = await self._signaler.createSendTransport(self._multimediaRuntime.sctpCapabilities.dict())
        logger.info('signal request: createWebRtcTransport, direction=send, requestId=%s', requestId)
        response = await self._signaler.getResponse(requestId)

        async def onConnect(dtlsParameters):
            requestIdToConnectSWT = await self._signaler.connectWebRtcTransport(self._multimediaRuntime.sendTransportId,
                                                                                dtlsParameters.dict(exclude_none=True))
            logger.info('signal request: connectWebRtcTransport, direction: send, requestId: %s', requestIdToConnectSWT)
            await self._signaler.getResponse(requestIdToConnectSWT)

        async def onProduce(kind: str, rtpParameters, appData: dict):
            requestIdToProduce = await self._signaler.produce(self._multimediaRuntime.sendTransportId, kind,
                                                              rtpParameters.dict(exclude_none=True), appData)
            logger.info('signal request: produce, requestId=%s', requestIdToProduce)
            response_ = await self._signaler.getResponse(requestIdToProduce)
            return response_.data['id']

        async def onProduceData(
                sctpStreamParameters,
                label: str,
                protocol: str,
                appData: dict
        ):
            requestIdToProduceData = await self._signaler.produceData(self._multimediaRuntime.sendTransportId, label,
                                                                      protocol,
                                                                      sctpStreamParameters.dict(exclude_none=True),
                                                                      appData)
            logger.info('signal request: produceData, requestId=%s', requestIdToProduceData)
            response_ = await self._signaler.getResponse(requestIdToProduceData)
            return response_.data['id']

        self._multimediaRuntime.createSendTransport(transportId=response.data['id'],
                                                    iceParameters=response.data['iceParameters'],
                                                    iceCandidates=response.data['iceCandidates'],
                                                    dtlsParameters=response.data['dtlsParameters'],
                                                    sctpParameters=response.data['sctpParameters'],
                                                    onConnectFunc=onConnect,
                                                    onProduceFunc=onProduce,
                                                    onProduceDataFunc=onProduceData)

    async def _createRecvTransport(self):
        if self._multimediaRuntime.recvTransportId is not None:
            logger.warn('the recvTransport has already been created')
            return
        requestId = await self._signaler.createRecvTransport(self._multimediaRuntime.sctpCapabilities.dict())
        logger.info('signal request: createWebRtcTransport, direction=recv, requestId=%s', requestId)
        response = await self._signaler.getResponse(requestId)

        async def onConnect(dtlsParameters):
            requestIdToConnectRWT = await self._signaler.connectWebRtcTransport(self._multimediaRuntime.recvTransportId,
                                                                                dtlsParameters.dict(exclude_none=True))
            logger.info('signal request: connectWebRtcTransport, direction: recv, requestId=%s', requestIdToConnectRWT)
            await self._signaler.getResponse(requestIdToConnectRWT)

        self._multimediaRuntime.createRecvTransport(transportId=response.data['id'],
                                                    iceParameters=response.data['iceParameters'],
                                                    iceCandidates=response.data['iceCandidates'],
                                                    dtlsParameters=response.data['dtlsParameters'],
                                                    sctpParameters=response.data['sctpParameters'],
                                                    onConnectFunc=onConnect)

    async def _joinFormally(self):
        requestId = await self._signaler.join(self._mePeer.data.displayName,
                                              self._mePeer.data.device,
                                              self._multimediaRuntime.rtpCapabilities.dict(exclude_none=True),
                                              self._multimediaRuntime.sctpCapabilities.dict(exclude_none=True))
        logger.info('signal request: join, requestId=%s', requestId)
        message = await self._signaler.getResponse(requestId)
        for peerInfo in message.data['peers']:
            self._room.addPeer(peerInfo['id'], data=PeerAppData(displayName=peerInfo['displayName'],
                                                                device=peerInfo['device']))

    # enableShare
    async def _produce(self):
        if not self._multimediaRuntime.canProduce:
            logger.warn('can\'t play, please check mediaFilePath and rtpCapabilities')
            return
        if self._multimediaRuntime.sendTransportId is None:
            await self._createSendTransport()
        await self._multimediaRuntime.produce()

        # record

    async def _consume(self, message: Request):
        if not self._multimediaRuntime.canConsume or not self._multimediaRuntime.autoConsume:
            return
        if self._multimediaRuntime.recvTransportId is None:
            await self._createRecvTransport()
        consumerId = message.data['id']
        peerId = message.data['peerId']
        producerPeer = self._mePeer.room.getPeerByPeerId(peerId)
        producerId = message.data['producerId']
        kind = message.data['kind']
        rtpParameters = message.data['rtpParameters']
        await self._multimediaRuntime.consume(self._mePeer, consumerId, producerPeer, producerId, kind, rtpParameters)
        otherPeer = self._room.getPeerByPeerId(peerId)
        self._room.bindConsumerIdToPeer(consumerId, otherPeer)
        requestId = message.requestId
        await self._consumerRequestListener.onNewConsumer(self._signaler.responseToNewConsumer(requestId), message,
                                                          otherPeer)

    async def _consumeData(self, message: Request):
        if self._multimediaRuntime.recvTransportId is None:
            await self._createRecvTransport()
        dataConsumerId = message.data['id']
        dataProducerId = message.data['dataProducerId']
        sctpStreamParameters = message.data['sctpStreamParameters']
        label = message.data['label']
        protocol = message.data['protocol']
        appData = message.data['appData']

        def onMessage(recvMessage):
            logger.info('DataChannel {%s}-{%s}: {%s}', label, protocol, recvMessage)
            self._dataConsumerNotificationListener.onMessage(otherPeer, recvMessage, label, protocol, appData)

        await self._multimediaRuntime.consumeData(dataConsumerId, dataProducerId, sctpStreamParameters, label, protocol,
                                                  appData, onMessage)
        otherPeer = self._room.getPeerByPeerId(message.data['peerId'])
        self._room.bindDataConsumerIdToPeer(dataConsumerId, otherPeer)
        requestId = message.requestId
        await self._dataConsumerRequestListener.onNewDataConsumer(self._signaler.responseToNewDataConsumer(requestId),
                                                                  message,
                                                                  otherPeer)

    async def _serverEventLoop(self):
        while True:
            message = await self._signaler.receiveMessage()
            if message.get('response'):
                logger.info('receive response for requestId: %d', message['id'])
                logger.debug('response details: ok=%s, data=%s', message['data'])
                self._signaler.setResponse(message)
            elif message.get('request'):
                logger.info('receive request, requestId=%d, method=%s', message['id'], message['method'])
                if message['method'] == MessageType.SERVER_REQURST_newConsumer.value:
                    # don't use: asyncio.create_task(self._consume(...))
                    # to prevent that consumer's notification precede it‘s request
                    await self._consume(Request(message['id'], message['method'], message['data']))
                elif message['method'] == MessageType.SERVER_REQURST_newDataConsumer.value:
                    await self._consumeData(Request(message['id'], message['method'], message['data']))
                else:
                    logger.error('unhandled request: %s' + message)
            elif message.get('notification'):
                logger.info('receive notification, method=%s', message['method'])
                if message['method'] in {MessageType.SERVER_NOTIFICATION_downlinkBwe.value}:
                    await self._bandwidthNotificationListener.enqueue(message)
                elif message['method'] in {MessageType.SERVER_NOTIFICATION_activeSpeaker.value,
                                           MessageType.SERVER_NOTIFICATION_newPeer.value,
                                           MessageType.SERVER_NOTIFICATION_peerDisplayNameChanged.value,
                                           MessageType.SERVER_NOTIFICATION_peerClosed.value}:
                    await self._peerNotificationListener.enqueue(message)
                elif message['method'] in {MessageType.SERVER_NOTIFICATION_producerScore.value}:
                    await self._producerNotificationListener.enqueue(message)
                elif message['method'] in {MessageType.SERVER_NOTIFICATION_consumerScore.value,
                                           MessageType.SERVER_NOTIFICATION_consumerLayersChanged.value,
                                           MessageType.SERVER_NOTIFICATION_consumerPaused.value,
                                           MessageType.SERVER_NOTIFICATION_consumerResumed.value,
                                           MessageType.SERVER_NOTIFICATION_consumerClosed.value}:
                    await self._consumerNotificationListener.enqueue(message)
                elif message['method'] in {MessageType.SERVER_NOTIFICATION_dataConsumerClosed.value}:
                    await self._dataConsumerNotificationListener.enqueue(message)
                else:
                    logger.error('unhandled notification: %s' + message)
            # bypass other no-exists message type
