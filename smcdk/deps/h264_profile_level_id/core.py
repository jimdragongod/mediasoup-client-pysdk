# h264-profile-level-id

# Profile
ProfileConstrainedBaseline = 1
ProfileBaseline = 2
ProfileMain = 3
ProfileConstrainedHigh = 4
ProfileHigh = 5

# Level
# All values are equal to ten times the level number, except level 1b which is
# special.
Level1_b = 0
Level1 = 10
Level1_1 = 11
Level1_2 = 12
Level1_3 = 13
Level2 = 20
Level2_1 = 21
Level2_2 = 22
Level3 = 30
Level3_1 = 31
Level3_2 = 32
Level4 = 40
Level4_1 = 41
Level4_2 = 42
Level5 = 50
Level5_1 = 51
Level5_2 = 52


class ProfileLevelId:
    def __init__(self, profile, level):
        self.profile = profile
        self.level = level

# Default ProfileLevelId.
#
# TODO: The default should really be profile Baseline and level 1 according to
# the spec: https://tools.ietf.org/html/rfc6184#section-8.1. In order to not
# break backwards compatibility with older versions of WebRTC where external
# codecs don't have any parameters, use profile ConstrainedBaseline level 3_1
# instead. This workaround will only be done in an interim period to allow
# external clients to update their code.
#
# http://crbug/webrtc/6337.
DefaultProfileLevelId = ProfileLevelId(ProfileConstrainedBaseline, Level3_1)

# For level_idc=11 and profile_idc=0x42, 0x4D, or 0x58, the constraint set3
# flag specifies if level 1b or level 1.1 is used.
ConstraintSet3Flag = 0x10

# Convert a string of 8 characters into a byte where the positions containing
# character c will have their bit set. For example, c = 'x', str = "x1xx0000"
# will return 0b10110000.
def byteMaskString(c, str):
    return (
        ((str[0] == c) << 7) | ((str[1] == c) << 6) | ((str[2] == c) << 5) |
        ((str[3] == c) << 4) | ((str[4] == c) << 3)    | ((str[5] == c) << 2)    |
        ((str[6] == c) << 1) | ((str[7] == c) << 0)
    )


# Class for matching bit patterns such as "x1xx0000" where 'x' is allowed to be
# either 0 or 1.
class BitPattern:
    def __init__(self, pattern):
        self._mask = ~byteMaskString('x', pattern)
        self._maskedValue = byteMaskString('1', pattern)
    
    def isMatch(self, value):
        return self._maskedValue == (value & self._mask)

class ProfilePattern:
    def __init__(self, profile_idc, profile_iop, profile):
        self.profile_idc = profile_idc
        self.profile_iop = profile_iop
        self.profile = profile

ProfilePatterns = [
    ProfilePattern(0x42, BitPattern('x1xx0000'), ProfileConstrainedBaseline),
    ProfilePattern(0x4D, BitPattern('1xxx0000'), ProfileConstrainedBaseline),
	ProfilePattern(0x58, BitPattern('11xx0000'), ProfileConstrainedBaseline),
	ProfilePattern(0x42, BitPattern('x0xx0000'), ProfileBaseline),
	ProfilePattern(0x58, BitPattern('10xx0000'), ProfileBaseline),
	ProfilePattern(0x4D, BitPattern('0x0x0000'), ProfileMain),
	ProfilePattern(0x64, BitPattern('00000000'), ProfileHigh),
	ProfilePattern(0x64, BitPattern('00001100'), ProfileConstrainedHigh)
]

# Parse profile level id that is represented as a string of 3 hex bytes.
# Nothing will be returned if the string is not a recognized H264 profile
# level id.
#
# @param {String} str - profile-level-id value as a string of 3 hex bytes.
#
# @returns {ProfileLevelId}
def parseProfileLevelId(level_id: str = None):
    if not level_id:
        return None
    
    if len(level_id) != 6:
        return None

    try:
        profile_level_id_numeric = int(level_id, 16)
    except ValueError:
        return None

    if profile_level_id_numeric == 0:
        return None
    
    level_idc = profile_level_id_numeric & 0xFF
    profile_iop = (profile_level_id_numeric >> 8) & 0xFF
    profile_idc = (profile_level_id_numeric >> 16) & 0xFF

    if (level_idc == Level1_1):
        level = Level1_b if (profile_iop & ConstraintSet3Flag) != 0 else Level1_1
    elif level_idc in [Level1, Level1_2, Level1_3, Level2, Level2_1, Level2_2, Level3, Level3_1, Level3_2, Level4, Level4_1, Level4_2, Level5, Level5_1, Level5_2]:
        level = level_idc
    else:
        return None
    
    # Parse profile_idc/profile_iop into a Profile enum.
    for pattern in ProfilePatterns:
        if profile_idc == pattern.profile_idc and pattern.profile_iop.isMatch(profile_iop):
            return ProfileLevelId(pattern.profile, level)
    
    return None

# Returns canonical string representation as three hex bytes of the profile
# level id, or returns nothing for invalid profile level ids.
#
# @param {ProfileLevelId} profile_level_id
#
# @returns {String}
def profileLevelIdToString(profile_level_id):
    if profile_level_id.level == Level1_b:
        if profile_level_id.profile == ProfileConstrainedBaseline:
            return '42f00b'
        elif profile_level_id.profile == ProfileBaseline:
            return '42100b'
        elif profile_level_id.profile == ProfileMain:
            return '4d100b'
        else:
            return None
    
    if profile_level_id.profile == ProfileConstrainedBaseline:
        profile_idc_iop_string = '42e0'
    elif profile_level_id.profile == ProfileBaseline:
        profile_idc_iop_string = '4200'
    elif profile_level_id.profile == ProfileMain:
        profile_idc_iop_string = '4d00'
    elif profile_level_id.profile == ProfileConstrainedHigh:
        profile_idc_iop_string = '640c'
    elif profile_level_id.profile == ProfileHigh:
        profile_idc_iop_string = '6400'
    else:
        return None
    
    return f'{profile_idc_iop_string}{profile_level_id.level:02x}'

# Parse profile level id that is represented as a string of 3 hex bytes
# contained in an SDP key-value map. A default profile level id will be
# returned if the profile-level-id key is missing. Nothing will be returned if
# the key is present but the string is invalid.
#
# @param {Object} [params={}] - Codec parameters object.
#
# @returns {ProfileLevelId}
def parseSdpProfileLevelId(params={}):
    profile_level_id = params.get('profile-level-id')
    return DefaultProfileLevelId if profile_level_id == None else parseProfileLevelId(profile_level_id)

# Returns True if the parameters have the same H264 profile, i.e. the same
# H264 profile (Baseline, High, etc).
#
# @param {Object} [params1={}] - Codec parameters object.
# @param {Object} [params2={}] - Codec parameters object.
#
# @returns {Boolean}
def isSameProfile(params1={}, params2={}):
    profile_level_id_1 = parseSdpProfileLevelId(params1)
    profile_level_id_2 = parseSdpProfileLevelId(params2)
    return profile_level_id_1 and profile_level_id_2 and (profile_level_id_1.profile == profile_level_id_2.profile)

# Generate codec parameters that will be used as answer in an SDP negotiation
# based on local supported parameters and remote offered parameters. Both
# local_supported_params and remote_offered_params represent sendrecv media
# descriptions, i.e they are a mix of both encode and decode capabilities. In
# theory, when the profile in local_supported_params represent a strict superset
# of the profile in remote_offered_params, we could limit the profile in the
# answer to the profile in remote_offered_params.
#
# However, to simplify the code, each supported H264 profile should be listed
# explicitly in the list of local supported codecs, even if they are redundant.
# Then each local codec in the list should be tested one at a time against the
# remote codec, and only when the profiles are equal should this function be
# called. Therefore, this function does not need to handle profile intersection,
# and the profile of local_supported_params and remote_offered_params must be
# equal before calling this function. The parameters that are used when
# negotiating are the level part of profile-level-id and level-asymmetry-allowed.
#
# @param {Object} [local_supported_params={}]
# @param {Object} [remote_offered_params={}]
#
# @returns {String} Canonical string representation as three hex bytes of the
#   profile level id, or null if no one of the params have profile-level-id.
#
# @throws {TypeError} If Profile mismatch or invalid params.
def generateProfileLevelIdForAnswer(local_supported_params={},remote_offered_params={}):
    if not local_supported_params.get('profile-level-id') and not remote_offered_params.get('profile-level-id'):
        return None
    
    local_profile_level_id = parseSdpProfileLevelId(local_supported_params)
    remote_profile_level_id = parseSdpProfileLevelId(remote_offered_params)

    # The local and remote codec must have valid and equal H264 Profiles.
    if not local_profile_level_id:
        raise TypeError('invalid local_profile_level_id')
    
    if not remote_profile_level_id:
        raise TypeError('invalid remote_profile_level_id')

    if local_profile_level_id.profile != remote_profile_level_id.profile:
        raise TypeError('H264 Profile mismatch')

    level_asymmetry_allowed = isLevelAsymmetryAllowed(local_supported_params) and isLevelAsymmetryAllowed(remote_offered_params)

    local_level = local_profile_level_id.level
    remote_level = remote_profile_level_id.level
    min_level = minLevel(local_level, remote_level)
    answer_level = local_level if level_asymmetry_allowed else min_level

    return profileLevelIdToString(ProfileLevelId(local_profile_level_id.profile, answer_level))

# Compare H264 levels and handle the level 1b case.
def isLessLevel(a, b):
    if a == Level1_b:
        return b != Level1 and b != Level1_b
    if b == Level1_b:
        return a != Level1
    return a < b

def minLevel(a, b):
    return a if isLessLevel(a, b) else b

def isLevelAsymmetryAllowed(params = {}):
    level_asymmetry_allowed = params.get('level-asymmetry-allowed')
    return level_asymmetry_allowed == 1 or level_asymmetry_allowed == '1'