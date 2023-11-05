from ShapeDiverTinySdkViktorUtils import ShapeDiverTinySessionSdkMemoized
from viktor.core import Storage
from viktor import File
import os

# ShapeDiver ticket and modelViewUrl
ticket = os.getenv("SD_TICKET")
if ticket is None or len(ticket) == 0:
    ticket = "a2dea6109cbcbe3b34906036c1c6bce1763adac8b1e25066af1ab69f5d715bfca562e9559d9f8e28f78756a545e3db3e1e29ea646423be87583ba0cd159b4806f8c26b48d12943be774af5cfd3d1eb5da4dbd19f163e7562cc17d823dcac2375e1446124ba732a36ca93094a1cacd4254ca2adfa222d5418-1c02a1b80a0b39bc36f136303faee4f2"
modelViewUrl = os.getenv("SD_MODEL_VIEW_URL")
if modelViewUrl is None or len(modelViewUrl) == 0:
    modelViewUrl = "https://nsc005.us-east-1.shapediver.com"


def ShapeDiverComputation(parameters):
 
    # Initialize a session with the model (memoized)
    shapeDiverSessionSdk = ShapeDiverTinySessionSdkMemoized(ticket, modelViewUrl)

    # compute outputs and exports of ShapeDiver model at the same time, 
    # get resulting glTF 2 assets and export assets
    result = shapeDiverSessionSdk.export(paramDict = parameters, includeOutputs = True)

    # get resulting exported asset of export called "BUILDING_STRUCTURE"
    exportItems1 = result.exportContentItems(exportName = "BUILDING_STRUCTURE")
    if len(exportItems1) != 1: 
        UserMessage.warning(f'No exported asset found for export "BUILDING_STRUCTURE".')
    else:
        Storage().set('BUILDING_STRUCTURE', data=File.from_url(exportItems1[0]['href']), scope='entity')
    
    # get resulting exported asset of export called "BUILDING_FLOOR_EDGE"
    exportItems2 = result.exportContentItems(exportName = "BUILDING_FLOOR_EDGE")
    if len(exportItems2) != 1: 
        UserMessage.warning(f'No exported asset found for export "BUILDING_FLOOR_EDGE".')
    else:
        Storage().set('BUILDING_FLOOR_EDGE', data=File.from_url(exportItems2[0]['href']), scope='entity')

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
