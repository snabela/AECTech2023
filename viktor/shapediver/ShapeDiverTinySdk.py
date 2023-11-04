import json
import requests

fileEndingToContentTypeMap = {
    "svg": "image/svg+xml",
    "svgz": "image/svg+xml",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tif": "image/tif",
    "tiff": "image/tiff",
    "hdr": "image/vnd.radiance",
    "gltf": "gltf+json",
    "glb": "model/gltf-binary",
    "bin": "application/octet-stream",
    "gltf": "model/gltf-binary",
    "3dm": "model/vnd.3dm",
    "3dm": "application/3dm",
    "3dm": "x-world/x-3dmf",
    "3ds": "application/x-3ds",
    "3ds": "image/x-3ds",
    "3ds": "application/3ds",
    "fbx": "application/fbx",
    "dxf": "application/dxf",
    "dxf": "application/x-autocad",
    "dxf": "application/x-dxf",
    "dxf": "drawing/x-dxf",
    "dxf": "image/vnd.dxf",
    "dxf": "image/x-autocad",
    "dxf": "image/x-dxf",
    "dxf": "zz-application/zz-winassoc-dxf",
    "dwg": "application/dwg",
    "pdf": "application/pdf",
    "3mf": "model/3mf",
    "stl": "model/stl",
    "stl": "application/sla",
    "amf": "application/amf",
    "ai": "application/ai",
    "dgn": "application/dgn",
    "ply": "application/ply",
    "ps": "application/postscript",
    "eps": "application/postscript",
    "skp": "application/skp",
    "slc": "application/slc",
    "sldprt": "application/sldprt",
    "sldasm": "application/sldasm",
    "stp": "application/step",
    "step": "application/step",
    "vda": "application/vda",
    "gdf": "application/gdf",
    "vrml": "model/vrml",
    "vrml": "model/x3d-vrml",
    "wrl": "model/vrml",
    "wrl": "model/x3d-vrml",
    "vi": "model/vrml",
    "vi": "model/x3d-vrml",
    "igs": "model/iges",
    "iges": "model/iges",
    "igs": "application/iges",
    "iges": "application/iges",
    "obj": "application/wavefront-obj",
    "obj": "model/obj",
    "off": "application/off",
    "txt": "text/plain",
    "mtl": "text/plain",
    "g": "text/plain",
    "gcode": "text/plain",
    "glsl": "text/plain",
    "csv": "text/csv",
    "csv": "application/vnd.ms-excel",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "rtf": "application/rtf",
    "zip": "application/zip",
    "xml": "application/xml",
    "xml": "text/xml",
    "json": "application/json",
    "ifc": "application/x-step",
    "ifcxml": "application/xml",
    "ifczip": "application/zip",
    "sdtf": "model/vnd.sdtf",
    "sddtf": "model/vnd.sdtf"
}

def mapFileEndingToContentType(fileEnding):
    if "." in fileEnding:
        fileEnding = fileEnding.split(".")[-1]
    if fileEnding in fileEndingToContentTypeMap.keys():
        return fileEndingToContentTypeMap[fileEnding]
    else:
        return None

def mapContentTypeToFileEnding(contentType):
    if contentType in fileEndingToContentTypeMap.values():
        for key, value in fileEndingToContentTypeMap.items():
            if value == contentType:
                return key
    else:
        return None

def ShapeDiverColorToRgb(sdColor):
    return tuple(int(sdColor[i:i+2],16) for i in (2, 4, 6))

def intToTwoDigitHex(i):
    return hex(i)[2:].rjust(2, '0')

def RgbToShapeDiverColor(r, g, b):
    return f"0x{intToTwoDigitHex(r)}{intToTwoDigitHex(g)}{intToTwoDigitHex(b)}ff"

def flatten_nested_list(nested_list):
    return [item for sublist in nested_list for item in (flatten_nested_list(sublist) if isinstance(sublist, list) else [sublist])]

class ShapeDiverResponse:
    """Wrapper for response objects from ShapeDiver Geometry Backend systems

    See API documentation: https://sdr7euc1.eu-central-1.shapediver.com/api/v2/docs/
    """

    def __init__(self, response):
        if isinstance(response, str):
            self.response = json.loads(response)
        else:
            self.response = response

    def parameters(self):
        """Parameter definitions

        Look for ResponseParameter in the API documentation.
        """

        return [value for (key, value) in self.response['parameters'].items()]

    def outputs(self):
        """Output definitions and results

        Look for ResponseOutput in the API documentation.
        """

        return [value for (key, value) in self.response['outputs'].items()]
       
    def outputContentItems(self):
        """Content resulting from outputs

        Look for ResponseOutputContent in the API documentation.
        """

        return flatten_nested_list([outputs['content'] for outputs in self.outputs()])

    def outputContentItemsGltf2(self):
        """glTF 2 content resulting from outputs

        Look for ResponseOutputContent in the API documentation.
        """

        return [item for item in self.outputContentItems() if item['contentType'] == 'model/gltf-binary']

    def exports(self):
        """Export definitions and results

        Look for ResponseExport in the API documentation.
        """

        return [value for (key, value) in self.response['exports'].items()]
    
    def exportContentItems(self):
        """Content resulting from exports

        Look for ResponseExportContent in the API documentation.
        """

        return flatten_nested_list([exports['content'] for exports in self.exports()])
    
    def sessionId(self):
        """Id of the session"""

        return self.response['sessionId']
    
    def assetFile(self, paramId):
        """Get upload URL and file id for a requested upload of a file parameter.
        
        The returned object contains properties 'id' and 'href'.
        """

        return self.response['asset']['file'][paramId]
    
def ExceptionHandler(func):
    """Decorator for activating the exception handler"""
    def decorate(*args, **kwargs):
        self = args[0]
        if hasattr(self, 'exceptionHandler'):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return self.exceptionHandler(e)
        if 'exceptionHandler' in kwargs:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return kwargs['exceptionHandler'](e)
        else:
            return func(*args, **kwargs)
    return decorate

def ParameterMapper(func):
    """Decorator for activating the parameter mapper"""
    def decorate(*args, **kwargs):
        self = args[0]
        if hasattr(self, 'parameterMapper') and 'paramDict' in kwargs:
            kwargs['paramDict'] = self.parameterMapper(paramDict = kwargs['paramDict'], sdk = self)
        return func(*args, **kwargs)
    return decorate

class ShapeDiverTinySessionSdk:
    """A minimal Python SDK to handle sessions with ShapeDiver Geometry Backend Systems.
    
    """

    @ExceptionHandler
    def __init__(self, *, modelViewUrl, ticket=None, sessionInitResponse=None, paramDict={}, exceptionHandler=None, parameterMapper=None):
        """Open a session with a ShapeDiver model
        
        Parameter values can optionally be included in the session init request.
        API documentation: https://sdr7euc1.eu-central-1.shapediver.com/api/v2/docs/#/session/post_api_v2_ticket__ticketId_
        """

        self.modelViewUrl = modelViewUrl

        if exceptionHandler is not None:
            self.exceptionHandler = exceptionHandler
      
        if parameterMapper is not None:
            self.parameterMapper = parameterMapper
      
        if sessionInitResponse is not None:
            self.response = ShapeDiverResponse(sessionInitResponse)
      
        elif ticket is not None:
            endpoint = f'{self.modelViewUrl}/api/v2/ticket/{ticket}'
            jsonBody = paramDict if isinstance(paramDict, str) else json.dumps(paramDict)
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(endpoint, data=jsonBody, headers=headers)
            if response.status_code != 201:
                raise Exception(f'Failed to open session (HTTP status code {response.status_code}): {response.text}')

            # TODO: handle rate-limiting and delay

            """Parsed response of the session init request"""
            self.response = ShapeDiverResponse(response.json())
        else:
            raise Exception('Expected (ticket and modelViewUrl) or (sessionInitResponse and modelViewUrl) to be provided')

    @ExceptionHandler
    def close(self):
        """Close the session
        
        API documentation: https://sdr7euc1.eu-central-1.shapediver.com/api/v2/docs/#/session/post_api_v2_session__sessionId__close
        """

        endpoint = f'{self.modelViewUrl}/api/v2/session/{self.response.sessionId()}/close'
        response = requests.post(endpoint);
        if response.status_code != 200:
            raise Exception(f'Failed to close session (HTTP status code {response.status_code}): {response.text}')

    @ExceptionHandler
    @ParameterMapper
    def output(self, *, paramDict = {}):
        """Request the computation of all outputs

        API documentation: https://sdr7euc1.eu-central-1.shapediver.com/api/v2/docs/#/output/put_api_v2_session__sessionId__output
        """

        endpoint = f'{self.modelViewUrl}/api/v2/session/{self.response.sessionId()}/output'
        jsonBody = json.dumps(paramDict)
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.put(endpoint, data=jsonBody, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Failed to compute outputs (HTTP status code {response.status_code}): {response.text}')

        # TODO: handle rate-limiting and delay

        return ShapeDiverResponse(response.json())

    @ExceptionHandler
    @ParameterMapper
    def export(self, *, exportId, paramDict = {}):
        """Request an export

        API documentation: https://sdr7euc1.eu-central-1.shapediver.com/api/v2/docs/#/export/put_api_v2_session__sessionId__export
        """

        endpoint = f'{self.modelViewUrl}/api/v2/session/{self.response.sessionId()}/export'
        body = {'exports': [exportId], 'parameters': paramDict}
        jsonBody = json.dumps(body)
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.put(endpoint, data=jsonBody, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Failed to compute export (HTTP status code {response.status_code}): {response.text}')

        # TODO: handle rate-limiting and delay

        return ShapeDiverResponse(response.json())
    
    @ExceptionHandler
    def requestFileUpload(self, *, requestBody = {}):
        """Request the upload of a file for a parameter of type 'File'

        API documentation: https://sdr7euc1.eu-central-1.shapediver.com/api/v2/docs/#/file/post_api_v2_session__sessionId__file_upload
        """

        endpoint = f'{self.modelViewUrl}/api/v2/session/{self.response.sessionId()}/file/upload'
        jsonBody = json.dumps(requestBody)
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(endpoint, data=jsonBody, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Failed to request file upload (HTTP status code {response.status_code}): {response.text}')

        # TODO: handle rate-limiting and delay

        return ShapeDiverResponse(response.json())
    