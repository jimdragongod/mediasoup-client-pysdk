import asyncio
import sys
from threading import Timer

from smcdk import *


def test_player(mediasoup_client_instance):
    print('player start...')
    mediasoup_client_instance.play()


# Please start mediasoup-demo/server before running this example.
# if you prefer to view the result of playing and recording,
# start mediasoup-demo/app and join room with the same roomId first
# you will watch the media file at producerConfig['mediaFilePath']
# enable mic and webCam, the recording file will be generated at consumerConfig['recordDirectoryPath']/[roomId]
if __name__ == '__main__':
    mediasoup_client = MediasoupClient()
    if sys.version_info.major == 3 and sys.version_info.minor == 6:
        loop = asyncio.get_event_loop()
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        # mock play in another thread, after 5 seconds
        timer = Timer(interval=5.0, function=test_player, args=[mediasoup_client])
        timer.start()

        print('MediasoupClient start...')
        loop.run_until_complete(
            mediasoup_client.joinRoom(
                roomAddressInfo={
                    # wss://[serverAddress]/?roomId=[roomId]&peerId=[peerId]
                    'serverAddress': '192.168.56.1:4443',
                    # if not specified, default is True
                    # set False at the local development environment, where a valid https certificate is not available
                    'enableSslVerification': False,
                    'roomId': '1'
                },
                peerInfo={
                    'peerId': 'sdkClient-001',
                    'displayName': 'jimDG'
                },
                producerConfig={
                    # if True, play automatically after joining room
                    'autoProduce': False,
                    # ensure that this media file exists
                    'mediaFilePath': 'D:/logs/video-audio-stereo.mp4',
                },
                consumerConfig={
                    # recording  automatically
                    'autoConsume': True,
                    'recordDirectoryPath': 'D:/logs'
                }))
    except KeyboardInterrupt:
        print('MediasoupClient shutdown')
    finally:
        loop.run_until_complete(mediasoup_client.close())
