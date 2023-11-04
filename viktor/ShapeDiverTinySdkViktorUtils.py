from viktor.utils import memoize
from viktor import UserError, UserMessage
from ShapeDiverTinySdk import ShapeDiverTinySessionSdk, RgbToShapeDiverColor, mapFileEndingToContentType
import json
import requests

def exceptionHandler(e):
    """VIKTOR-specific exception handler to use for ShapeDiverTinySessionSdk
    
    Adapt this if you want to handle exceptions differently.
    """

    message = e.args[0]
    UserMessage.warning(message)
    raise UserError(message)

@memoize
def __ShapeDiverSessionInitResponseMemoized(ticket, modelViewUrl):
    """Adds support for memoizing ShapeDiver sessions

    see https://docs.viktor.ai/sdk/api/utils/#_memoize
    """

    sdk = ShapeDiverTinySessionSdk(ticket = ticket, modelViewUrl = modelViewUrl, exceptionHandler = exceptionHandler)
    return json.dumps(sdk.response.response)

def parameterMapper(*, paramDict, sdk):
    """Map VIKTOR parameter values to ShapeDiver
    
    This is used to map special value types like Color or File.
    """

    paramDictSd = {}
    paramIds = [key for (key, value) in paramDict.items()]
    for paramId in paramIds:
        value = paramDict[paramId]
        if value is None:
            continue
        if paramId in sdk.response.response['parameters']:
            paramDef = sdk.response.response['parameters'][paramId]
            if paramDef['type'] == 'Color':
                color = value
                paramDictSd[paramId] = RgbToShapeDiverColor(color.r, color.g, color.b)
            elif paramDef['type'] == 'File':
                # See Viktor FileField and File object
                # https://docs.viktor.ai/sdk/api/parametrization/#FileField
                # https://docs.viktor.ai/sdk/api/core/#_File
                # Note: Reading the whole file into memory, like done in the following, 
                #       might cause problems in case of big files.
                fileBinaryContent = value.file.getvalue_binary()
                # request file upload to ShapeDiver Geometry Backend
                # we simply use the first allowed content-type (mapping of file ending to content-type to be implemented)
                body = {}
                body[paramId] = {}
                body[paramId]['size'] = len(fileBinaryContent)
                body[paramId]['format'] = mapFileEndingToContentType(value.filename)
                uploadResponse = sdk.requestFileUpload(requestBody = body).assetFile(paramId)
                # upload the file
                headers = {
                    'Content-Type': body[paramId]['format']
                }
                response = requests.put(uploadResponse['href'], data=fileBinaryContent, headers=headers)
                if response.status_code != 200:
                    raise Exception(f'Failed to put file (HTTP status code {response.status_code}): {response.text}')
                # set parameter value to id of uploaded file
                paramDictSd[paramId] = uploadResponse['id']
                # TODO memoize id of uploaded file based on hash of file contents and parameter id
            else:
                paramDictSd[paramId] = value
        else:
            paramDictSd[paramId] = value

    return paramDictSd

def ShapeDiverTinySessionSdkMemoized(ticket, modelViewUrl, forceNewSession=False):
    """Memoized version of ShapeDiverTinySessionSdk
    
    Use this instead of ShapeDiverTinySessionSdk to prevent a new ShapeDiver session
    being created for every computation or export. 
    """

    if forceNewSession: 
        sdk = ShapeDiverTinySessionSdk(ticket = ticket, modelViewUrl = modelViewUrl, 
            exceptionHandler = exceptionHandler, parameterMapper = parameterMapper)
    else:
        response = __ShapeDiverSessionInitResponseMemoized(ticket = ticket, modelViewUrl = modelViewUrl)
        sdk = ShapeDiverTinySessionSdk(sessionInitResponse = response, modelViewUrl = modelViewUrl, 
            exceptionHandler = exceptionHandler, parameterMapper = parameterMapper)
    return sdk

