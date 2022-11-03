from .core import *

class h264_profile_level_id:
    @staticmethod
    def isSameProfile(params1={}, params2={}):
        return isSameProfile(params1,params2)

    @staticmethod
    def generateProfileLevelIdForAnswer(local_supported_params={},remote_offered_params={}):
        return generateProfileLevelIdForAnswer(local_supported_params,remote_offered_params)
