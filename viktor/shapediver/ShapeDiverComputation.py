import json

from viktor.core import Storage
from viktor import File, UserMessage, UserError
import os

# ShapeDiver ticket and modelViewUrl
from shapediver.ShapeDiverTinySdkViktorUtils import ShapeDiverTinySessionSdkMemoized

ticket = os.getenv("SD_TICKET")
if ticket is None or len(ticket) == 0:
    ticket = "b226b6ce238e16f8a08f6aa9c5e714ca5c002b414e04b4ae196e63385d212915c7f578379b02e048c5966c7442a3129e528116ae45b8bf513c7bf4892116770c76380a0c90135065ef5c87a5f1ca2a770198510198042486ad26e5cbc7a5af9a07fe552df74dd1e1a798f97b95eef832952c30b3b5a62e23-362022f1a76d8c3ea7d7496cbe8d8a16"
modelViewUrl = os.getenv("SD_MODEL_VIEW_URL")
if modelViewUrl is None or len(modelViewUrl) == 0:
    modelViewUrl = "https://nsc005.us-east-1.shapediver.com"


def ShapeDiverComputation(parameters):
 
    # Initialize a session with the model (memoized)
    shapeDiverSessionSdk = ShapeDiverTinySessionSdkMemoized(ticket, modelViewUrl, forceNewSession = True)

    # compute outputs and exports of ShapeDiver model at the same time, 
    # get resulting glTF 2 assets and export assets
    result = shapeDiverSessionSdk.export(paramDict = parameters, includeOutputs = True)

    # get resulting exported asset of export called "BUILDING_STRUCTURE"
    exportItems = result.exportContentItems(exportName = "BUILDING_STRUCTURE")
    if len(exportItems) != 1: 
        UserMessage.warning(f'No exported asset found for export "BUILDING_STRUCTURE".')
    else:
        Storage().set('BUILDING_STRUCTURE', data=File.from_url(exportItems[0]['href']), scope='entity')
    
    # get resulting exported asset of export called "BUILDING_FLOOR_EDGE"
    exportItems = result.exportContentItems(exportName = "BUILDING_FLOOR_EDGE")
    if len(exportItems) != 1: 
        UserMessage.warning(f'No exported asset found for export "BUILDING_FLOOR_EDGE".')
    else:
        Storage().set('BUILDING_FLOOR_EDGE', data=File.from_url(exportItems[0]['href']), scope='entity')

    # get resulting exported asset of export called "BUILDING_FLOOR_ELV_AREA"
    exportItems = result.exportContentItems(exportName = "BUILDING_FLOOR_ELV_AREA")
    if len(exportItems) != 1: 
        UserMessage.warning(f'No exported asset found for export "BUILDING_FLOOR_ELV_AREA".')
    else:
        Storage().set('BUILDING_FLOOR_ELV_AREA', data=File.from_url(exportItems[0]['href']), scope='entity')

    # get glTF2 output
    contentItemsGltf2 = result.outputContentItemsGltf2()
    
    if len(contentItemsGltf2) < 1:
        raise UserError('Computation did not result in at least one glTF 2.0 asset.')
    
    if len(contentItemsGltf2) > 1: 
        UserMessage.warning(f'Computation resulted in {len(contentItemsGltf2)} glTF 2.0 assets, only displaying the first one.')

    glTF_url = contentItemsGltf2[0]['href']
    Storage().set('GLTF_URL', data=File.from_data(glTF_url), scope='entity')

    glTF_file = File.from_url(glTF_url)

    return glTF_file


def ShapeDiverComputationForOptimization(parameters):
    # Initialize a session with the model (memoized)
    shapeDiverSessionSdk = ShapeDiverTinySessionSdkMemoized(ticket, modelViewUrl, forceNewSession=True)

    # compute outputs and exports of ShapeDiver model at the same time,
    # get resulting glTF 2 assets and export assets
    result = shapeDiverSessionSdk.export(paramDict=parameters, includeOutputs=True)

    # get resulting exported asset of export called "BUILDING_STRUCTURE"
    exportItems = result.exportContentItems(exportName="BUILDING_STRUCTURE")
    if len(exportItems) != 1:
        UserMessage.warning(f'No exported asset found for export "BUILDING_STRUCTURE".')
    else:
        BUILDING_STRUCTURE = json.loads(File.from_url(exportItems[0]['href']).getvalue())

    # get resulting exported asset of export called "BUILDING_FLOOR_ELV_AREA"
    exportItems = result.exportContentItems(exportName="BUILDING_FLOOR_ELV_AREA")
    if len(exportItems) != 1:
        UserMessage.warning(f'No exported asset found for export "BUILDING_FLOOR_ELV_AREA".')
    else:
        BUILDING_FLOOR_ELV_AREA = json.loads(File.from_url(exportItems[0]['href']).getvalue())

    return BUILDING_STRUCTURE, BUILDING_FLOOR_ELV_AREA
