from ShapeDiverTinySdkViktorUtils import ShapeDiverTinySessionSdkMemoized
from viktor.core import Storage
from viktor import File, UserMessage
import os

# ShapeDiver ticket and modelViewUrl
ticket = os.getenv("SD_TICKET")
if ticket is None or len(ticket) == 0:
    ticket = "36cdfeb2dbf22539f4dd18593c2c0df2f1ae5f244078fdc784e72deb6b95601e09903a76c02e499314595a1e77d622dd93110b9cb58b3f48c9ff315e7cb406663f7c98855823a66b9b0ad099fe98e845d01cb851e182dba9e1c5f833d8ab2b7772c9255399decda02c33e8cd0f6b4165c6154d54216af0b1-7aae369e1e8a0c95a29d4c4060daee89"
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
