import base64
import json

def returnData(fieldName,data):
    if fieldName in data.keys():
        return data[fieldName]
    else:
        return None


def isStringFound(string, content):
    return (string.lower() in content.lower())


def encrypt(value):
    return_value = base64.encodebytes(value.encode())
    return_value = return_value[2:len(return_value)-1] + return_value[0:2] + return_value[len(return_value)-1:]
    return return_value


def decrypt(value):
    try:
        encoded = value.encode()
    except:
        encoded = value
    return_value = encoded[len(encoded)-3:].replace(b'\n',b'') + encoded[0:len(encoded)-3] + encoded[len(encoded)-1:]
    return_value = base64.decodebytes(return_value)
    return return_value.decode()


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------
class GenericJsonObject(object):
    def __init__(self, co):
        self.__dict__ = json.loads(co)

    def get_value(self, fields, default_value):
        levels = fields.split('|')
        return_value = default_value
        for idx in range(0, len(levels)):
            if idx == 0:
                obj = self.__dict__
            else:
                obj = obj[levels[idx-1]]

            if levels[idx] not in obj.keys():
                break
            else:
                if (idx+1) == len(levels):
                    if isinstance(obj[levels[idx]], bool):
                        return_value = (1 if obj[levels[idx]] else 0)
                    else:
                        return_value = obj[levels[idx]]
                    break
        return return_value