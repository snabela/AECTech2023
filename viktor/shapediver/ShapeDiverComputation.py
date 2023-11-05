from viktor.core import Storage
from viktor import File, UserMessage, UserError
import os

# ShapeDiver ticket and modelViewUrl
from shapediver.ShapeDiverTinySdkViktorUtils import ShapeDiverTinySessionSdkMemoized

ticket = os.getenv("SD_TICKET")
if ticket is None or len(ticket) == 0:
    ticket = "567ca9d3794efdaf984a64f8410656443d7bfbfb8dd358a00c392d78b62bc0f32b22f6a2d9a9cf5ec92ba4de82ca5a60f91b2339100f9136e43509a4b34276fac32da1f35227c2167685b3436de987579f76b7e8fa62417a450d51233e390ed954969a99c95f342aeff027c72364700afe02500b99d00026-0cfb869c3094ede7c31fa4c242b5278a"
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
