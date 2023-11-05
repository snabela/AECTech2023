import os
import sys
import comtypes.client
import json

# Launch ETABS and get SapModel
def launchETABS(programPath, modelPath, modelName):

    ModelPath = modelPath + os.sep + modelName + '.edb'
    helper = comtypes.client.CreateObject('ETABSv1.Helper')
    helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)

    try:
        #'create an instance of the ETABS object from the specified path
        myETABSObject = helper.CreateObject(programPath)
    except (OSError, comtypes.COMError):
        print('Cannot start a new instance of the program from ' + programPath)
        sys.exit(-1)
        
    #start ETABS application
    myETABSObject.ApplicationStart()

    #create SapModel object
    SapModel = myETABSObject.SapModel
    ret = SapModel.File.OpenFile(ModelPath)
    ret = SapModel.SetPresentUnits(2) # 1 for lb/in, use 2 for lb/ft

    # Save the current model as a new file with the new name
    ret = SapModel.File.Save(os.path.join(modelPath, 'Test' + '.EDB'))

    return SapModel

# Clean up everything after running
def cleanUp():
    SapModel = None
    myETABSObject = None

# Function to read and process the building structure from a JSON file
def process_building_structure(file_path):
    # Dictionaries to store the processed information
    nodeInfo = {}
    beamInfo = {}
    floorInfo = {}
    levelInfo = {}

    # Read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Process nodes (assuming every 3 values in the list represent x, y, z coordinates of a node)
    node_counter = 1
    for i in range(0, len(data['nodes']), 3):
        x, y, z = data['nodes'][i:i+3]
        nodeInfo[node_counter] = [round(float(coord), 3) for coord in [x, y, z]]
        node_counter += 1

    # Process beams (assuming each entry in beams is a list of node numbers for that beam)
    beam_counter = 1
    for beam_nodes in data['beams']:
        beamInfo[beam_counter] = [int(node_number) for node_number in beam_nodes]
        beam_counter += 1

    # Process floors (assuming each entry in floors is a list of node numbers for that floor)
    floor_counter = 1
    for floor_nodes in data['floors']:
        floorInfo[floor_counter] = [int(node_number) for node_number in floor_nodes]
        floor_counter += 1

    # Infer levels from the unique z values (excluding the base level at z=0)
    z_values = sorted({coord[2] for coord in nodeInfo.values() if coord[2] > 0})
    levelInfo = {f"Level{i+1}": round(z, 3) for i, z in enumerate(z_values)}

    return nodeInfo, beamInfo, floorInfo, levelInfo

# Create all data in ETABS
def createDataInETABS(levelInfo, nodeInfo, lineInfo, floorInfo, wallInfo):
    # Create Levels in ETABS
    levelNames = list(levelInfo.keys())
    levelElevations = list(levelInfo.values())
    createLevels(SapModel, levelNames, levelElevations)

    # Create Nodes in ETABS
    for nodeName, coords in nodeInfo.items():
        x, y, z = coords
        createNode(SapModel, x, y, z)

    # Create Lines in ETABS
    for lineName, nodes in lineInfo.items():
        node1, node2 = nodes
        createLine(SapModel, node1, node2)

    # Create Areas (Floors) in ETABS
    for floorName, nodesList in floorInfo.items():
        createArea(SapModel, nodesList)

# Create Levels in ETABS
def createLevels(SapModel,levelNames,levelElevations):
    ret = SapModel.Story.SetStories_2(0,len(levelNames),levelNames,levelElevations,
                                      [False for i in range(len(levelNames))],
                                      ['' for i in range(len(levelNames))],
                                      [False for i in range(len(levelNames))],
                                      [0.0 for i in range(len(levelNames))],
                                      [0 for i in range(len(levelNames))])

# Create Node in ETABS
def createNode(SapModel,x,y,z):
    MyName = ""
    Name = ""
    ret = SapModel.PointObj.AddCartesian(x, y, z, Name, MyName)

# Create Line (Column/Beam) in ETABS
def createLine(SapModel,node1,node2):
    Name = ""
    ret = SapModel.FrameObj.AddByPoint(node1, node2, Name)

# Create area  in ETABS
def createArea(SapModel,nodesList):
    ret = SapModel.AreaObj.AddByPoint(4, nodesList, '')

# 
def createResultsFileforViktor(SapModel):
    print("hello")

# ETABS Installation location
programPath = 'D:\Computers and Structures\ETABS 21\ETABS.exe'

# Location and name of data from Victor
dataFileFromVictor = 'D:\\Repo\\AECTech2023\\viktor\\structural\\building_structure.json'

# Launch ETABS
SapModel = launchETABS(programPath, 'D:\\Repo\\AECTech2023\\viktor\\structural\\analysismodel', 'Template')

# Read data from Victor
# levelInfo, nodeInfo, lineInfo, floorInfo, wallInfo = process_building_structure(dataFileFromVictor)

# createDataInETABS(levelInfo, nodeInfo, lineInfo, floorInfo, wallInfo)

# TO DO:
# Applying Supports
# Applying loads at all levels

# Run Analysis
# Create Results file for Victor

# readDataFromVictor(dataFileFromVictor)
cleanUp()





