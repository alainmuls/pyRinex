import sys


# observables in RINEX v3.02
def find_values_for_key(key: str, d: dict) -> str:
    """
    find the value of a key in a nested dict
    """
    for k, v in d.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find_values_for_key(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in find_values_for_key(key, d):
                    yield result


def find_keys_for_value(value: str, d: dict) -> str:
    """
    find the key of a value in a nested dict
    """
    for k, v in d.items():
        if v == value:
            yield k
        elif isinstance(v, dict):
            for result in find_keys_for_value(value, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in find_keys_for_value(value, v):
                    yield result


def find_dict_for_value(value: str, d: dict) -> str:
    """
    find the key of a value in a nested dict
    """
    for k, v in d.items():
        if v == value:
            yield d
        elif isinstance(v, dict):
            for result in find_keys_for_value(value, v):
                yield v
        elif isinstance(v, list):
            for d in v:
                for result in find_keys_for_value(value, v):
                    yield v


# def grab_children(father):
#     local_list = []
#     for key, value in father.items():
#         local_list.append(key)
#         if isinstance(value, dict):
#             local_list.extend(grab_children(value))
#     return local_list


def walk(d: dict, path: list, value: str) -> str:
    """
    walks trhough nested dict to find dict with' value'
    """
    global path2Dict
    for k,v in d.items():
        # print('{k!r} -> {v!r}'.format(k=k, v=v))
        if isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
            # print('1. appending {k!r}'.format(k=k))
            path.append(k)
            # print("{}={}".format(".".join(path), v))
            # print('check {v!r} == {value!r}: {tf!r}'.format(v=v, value=value, tf=(v==value)))
            if v == value:
                # print('return {}={}'.format('.'.join(path), v))
                path2Dict = '{}={}'.format('.'.join(path), v)
                # mystr += "{}={}".format(".".join(path), v)
            path.pop()
        elif v is None:
            # print('2. appending {k!r}'.format(k=k))
            path.append(k)
            ## do something special
            path.pop()
        elif isinstance(v, dict):
            # print('3. appending {k!r}'.format(k=k))
            path.append(k)
            walk(v, path, value)
            path.pop()
        else:
            print("###Type {!s} not recognized: {!s}.{!s}={!s}".format(type(v), ".".join(path),k, v))


# def dictionary_check(input: dict):
#     """
#     First prints the final entry in the dictionary (most nested) and its key
#     Then prints the keys leading into this
#     * could be reversed to be more useful, I guess
#     """
#     for key,value in input.items():
#         if isinstance(value, dict):
#             dictionary_check(value)
#             print(key)
#         else:
#             print(key, value)


# def find(value: str, d: dict):
#     return {outer_key: inner_val for outer_key, outer_val in d.items() for inner_key, inner_val in outer_val.items() if inner_val == value}
# def find(label, data):
#     return {outer_key: inner_val for outer_key, outer_val in data.items() for inner_key, inner_val in outer_val.items() if inner_value == label}


# def iterdict(d):
#     for k,v in d.items():
#         if isinstance(v, dict):
#             iterdict(v)
#         else:
#             print('key {:s} for value {:s}'.format(k, v))


def findSignalsOfType(signalType: str, dGNSS: dict) -> list:
    """
    findSIgnalsOfType parses dict to find all signals of the specified type (PR, CP, DF or SS)
    """
    return list(find_values_for_key(signalType, dGNSS))


def findKeyOfSignal(signal: str, dGNSS: dict) -> list:
    """
    findKeyOfSignal finds to what signalType (so key) a specific signal belongs
    """
    return list(find_keys_for_value(signal, dGNSS))


# GNSS
dGNSSsIDs = {
    'G': 'GPS',
    'R': 'GLONASS',
    'S': 'SBAS payload',
    'E': 'Galileo',
    'C': 'Compass'
}

dSignalTypesNames = {
    'PR': {'name': 'Pseudo-Range', 'unit': '[m]'},
    'CP': {'name': 'Carrier Phase', 'unit': '[-]'},
    'DF': {'name': 'Doppler Frequency', 'unit': '[Hz]'},
    'SS': {'name': 'Signal Strength', 'unit': '[dB-Hz]'}
}

# L1 channels
dL1CA = {
    'name': 'Coarse/Acquisition code',
    'PR': 'C1C',
    'CP': 'L1C',
    'DF': 'D1C',
    'SS': 'S1C'
}

dL1CD = {
    'name': 'L1 Civilian (Data)',
    'PR': 'C1S',
    'CP': 'L1S',
    'DF': 'D1S',
    'SS': 'S1S'
}

dL1CP = {
    'name': 'L1 Civilian (Pilot)',
    'PR': 'C1L',
    'CP': 'L1L',
    'DF': 'D1L',
    'SS': 'S1L'
}


dL1CDP = {
    'name': 'L1 Civilian (Data & Pilot)',
    'PR': 'C1X',
    'CP': 'L1X',
    'DF': 'D1X',
    'SS': 'S1X'
}

dL1P = {
    'name': 'Precision code',
    'PR': 'C1P',
    'CP': 'L1P',
    'DF': 'D1P',
    'SS': 'S1P'
}

dL1Z = {
    'name': 'Z-tracking',
    'PR': 'C1W',
    'CP': 'L1W',
    'DF': 'D1W',
    'SS': 'S1W'
}

dL1Y = {
    'name': 'Encrypted (Precision) code',
    'PR': 'C1Y',
    'CP': 'L1Y',
    'DF': 'D1Y',
    'SS': 'S1Y'
}

dL1M = {
    'name': 'Military code',
    'PR': 'C1M',
    'CP': 'L1M',
    'DF': 'D1M',
    'SS': 'S1M'
}

dL1Codeless = {
    'name': 'Codeless',
    'PR': '',
    'CP': 'L1N',
    'DF': 'D1N',
    'SS': 'S1N'
}

# L2 channels
dL2CA = {
    'name': 'Coarse/Acquisition code',
    'PR': 'C2C',
    'CP': 'L2C',
    'DF': 'D2C',
    'SS': 'S2C'
}

dCAP2P1 = {
    'name': 'semi-codeless',
    'PR': 'C2D',
    'CP': 'L2D',
    'DF': 'D2D',
    'SS': 'S2D'
}

dL2CD = {
    'name': 'L2 Civilian (Data)',
    'PR': 'C2S',
    'CP': 'L2S',
    'DF': 'D2S',
    'SS': 'S2S'
}

dL2CP = {
    'name': 'L2 Civilian (Pilot)',
    'PR': 'C2L',
    'CP': 'L2L',
    'DF': 'D2L',
    'SS': 'S2L'
}


dL2CDP = {
    'name': 'L2 Civilian (Data & Pilot)',
    'PR': 'C2X',
    'CP': 'L2X',
    'DF': 'D2X',
    'SS': 'S2X'
}

dL2P = {
    'name': 'Precision code',
    'PR': 'C2P',
    'CP': 'L2P',
    'DF': 'D2P',
    'SS': 'S2P'
}

dL2Z = {
    'name': 'Z-tracking',
    'PR': 'C2W',
    'CP': 'L2W',
    'DF': 'D2W',
    'SS': 'S2W'
}

dL2Y = {
    'name': 'Encrypted (Precision) code',
    'PR': 'C2Y',
    'CP': 'L2Y',
    'DF': 'D2Y',
    'SS': 'S2Y'
}

dL2M = {
    'name': 'Military code',
    'PR': 'C2M',
    'CP': 'L2M',
    'DF': 'D2M',
    'SS': 'S2M'
}

dL2Codeless = {
    'name': 'Codeless',
    'PR': '',
    'CP': 'L2N',
    'DF': 'D2N',
    'SS': 'S2N'
}

# L5 Frequency band
dL5I = {
    'name': 'SoL (Data)',
    'PR': 'C5I',
    'CP': 'L5I',
    'DF': 'D5I',
    'SS': 'S5I'
}

dL5Q = {
    'name': 'SoL (Pilot)',
    'PR': 'C5Q',
    'CP': 'L5Q',
    'DF': 'D5Q',
    'SS': 'S5Q'
}

dL5IQ = {
    'name': 'SoL (Data+Pilot)',
    'PR': 'C5X',
    'CP': 'L5X',
    'DF': 'D5X',
    'SS': 'S5X'
}



dGPS = {
    'name': 'GPS-NavSTAR',
    'L1': {
        'freq': 1575.42,
        'CA': dL1CA,
        'L1C(D)': dL1CD,
        'L1C(P)': dL1CP,
        'L1C(D+P)': dL1CDP,
        'P': dL1P,
        'Z': dL1Z,
        'Y': dL1Y,
        'M': dL1M,
        'Codeless': dL1Codeless
    },
    'L2': {
        'freq': 1227.60,
        'CA': dL2CA,
        'Semi-codeless': dCAP2P1,
        'L2C(D)': dL2CD,
        'L2C(P)': dL2CP,
        'L2C(D+P)': dL2CDP,
        'P': dL2P,
        'Z': dL2Z,
        'Y': dL2Y,
        'M': dL2M,
        'Codeless': dL2Codeless
    },
    'L5': {
        'freq': 1176.45,
        'I': dL5I,
        'Q': dL5Q,
        'I+Q': dL5IQ,
    }
}


# GALILEO

# E1 channel
dE1A = {
    'name': 'PRS',
    'PR': 'C1A',
    'CP': 'L1A',
    'DF': 'D1A',
    'SS': 'S1A'
}

dE1B = {
    'name': 'I/NAV OS/CS/SoL',
    'PR': 'C1B',
    'CP': 'L1B',
    'DF': 'D1B',
    'SS': 'S1B'
}

dE1C = {
    'name': 'C (no data)',
    'PR': 'C1C',
    'CP': 'L1C',
    'DF': 'D1C',
    'SS': 'S1C'
}

dE1BC = {
    'name': 'B+C',
    'PR': 'C1X',
    'CP': 'L1X',
    'DF': 'D1X',
    'SS': 'S1X'
}

dE1ABC = {
    'name': 'A+B+C',
    'PR': 'C1Z',
    'CP': 'L1Z',
    'DF': 'D1Z',
    'SS': 'S1Z'
}


dE5AI = {
    'name': 'F/NAV OS',
    'PR': 'C5I',
    'CP': 'L5I',
    'DF': 'D5I',
    'SS': 'S5I'
}

dE5AQ = {
    'name': 'no data',
    'PR': 'C5Q',
    'CP': 'L5Q',
    'DF': 'D5Q',
    'SS': 'S5Q'
}

dE5AIQ = {
    'name': 'I+Q',
    'PR': 'C5X',
    'CP': 'L5X',
    'DF': 'D5X',
    'SS': 'S5X'
}

dE5BI = {
    'name': 'I/NAV OS/CS/SoL',
    'PR': 'C7I',
    'CP': 'L7I',
    'DF': 'D7I',
    'SS': 'S7I'
}

dE5BQ = {
    'name': 'no data',
    'PR': 'C7Q',
    'CP': 'L7Q',
    'DF': 'D7Q',
    'SS': 'S7Q'
}

dE5BIQ = {
    'name': 'I+Q',
    'PR': 'C7X',
    'CP': 'L7X',
    'DF': 'D7X',
    'SS': 'S7X'
}

dE5I = {
    'name': 'I',
    'PR': 'C8I',
    'CP': 'L8I',
    'DF': 'D8I',
    'SS': 'S8I'
}

dE5Q = {
    'name': 'no data',
    'PR': 'C8Q',
    'CP': 'L8Q',
    'DF': 'D8Q',
    'SS': 'S8Q'
}

dE5IQ = {
    'name': 'I+Q',
    'PR': 'C8X',
    'CP': 'L8X',
    'DF': 'D8X',
    'SS': 'S8X'
}


dE6A = {
    'name': 'PRS',
    'PR': 'C6A',
    'CP': 'L6A',
    'DF': 'D6A',
    'SS': 'S6A'
}

dE6B = {
    'name': 'I/NAV OS/CS/SoL',
    'PR': 'C6B',
    'CP': 'L6B',
    'DF': 'D6B',
    'SS': 'S6B'
}

dE6C = {
    'name': 'C (no data)',
    'PR': 'C6C',
    'CP': 'L6C',
    'DF': 'D6C',
    'SS': 'S6C'
}

dE6BC = {
    'name': 'B+C',
    'PR': 'C6X',
    'CP': 'L6X',
    'DF': 'D6X',
    'SS': 'S6X'
}

dE6ABC = {
    'name': 'A+B+C',
    'PR': 'C6Z',
    'CP': 'L6Z',
    'DF': 'D6Z',
    'SS': 'S6Z'
}


dGAL = {
    'name': 'Galileo',
    'E1': {
        'freq': 1575.42,
        'E1A': dE1A,
        'E1B': dE1B,
        'E1C': dE1C,
        'E1BC': dE1BC,
        'E1ABC': dE1ABC
    },
    'E5a': {
        'freq': 1176.45,
        'E5AI': dE5AI,
        'E5AQ': dE5AQ,
        'E5AIQ': dE5AIQ
    },
    'E5b': {
        'freq': 1207.14,
        'E5BI': dE5BI,
        'E5BQ': dE5BQ,
        'E5BIQ': dE5BIQ
    },
    'E5AB': {
        'freq': 1191.795,
        'E5I': dE5I,
        'E5Q': dE5Q,
        'E5IQ': dE5IQ
    },
    'E6': {
        'freq': 1278.75,
        'E6A': dE6A,
        'E6B': dE6B,
        'E6C': dE6C,
        'E6BC': dE6BC,
        'E6ABC': dE6ABC
    }
}
