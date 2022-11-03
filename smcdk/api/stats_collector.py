# todo: my design hasn't finished yet，(⊙﹏⊙)
# local：collect statistics from local webrtc device, e.g. browser
# remote：collect statistics from mediasoup server side
class StatsCollector:
    def __init__(self):
        pass

    def onGetSendTransportRemoteStats(self):
        pass

    def onGetSendTransportLocalStats(self):
        pass

    def onGetRecvTransportRemoteStats(self):
        pass

    def onGetRecvTransportLocalStats(self):
        pass

    def onGetAudioRemoteStats(self):
        # onGetProducerStats
        pass

    def onGetAudioLocalStats(self):
        pass

    def onGetVideoRemoteStats(self):
        # onGetProducerStats
        pass

    def onGetVideoLocalStats(self):
        pass

    def onGetConsumerLocalStats(self):
        pass

    def onGetConsumerRemoteStats(self):
        pass

    def onGetDataProducerRemoteStats(self):
        pass

    def onGetDataConsumerRemoteStats(self):
        pass
