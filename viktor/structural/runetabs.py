import os
import sys
import comtypes.client

# Launch ETABS and get SapModel
def launchETABS(programPath, modelPath, modelName):
    if not os.path.exists(modelPath):
        os.makedirs(modelPath)
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
    SapModel.InitializeNewModel()
    ret = SapModel.File.NewBlank()
    ret = SapModel.SetPresentUnits(2) # 1 for lb/in, use 2 for lb/ft

    return SapModel

# Clean up everything after running
def cleanUp():
    SapModel = None
    myETABSObject = None

# Read data from Victor File
def readDataFromViktor(filePath):
    levelInfo = {}
    nodeInfo = {}
    lineInfo = {}
    areaInfo = {}
    wallInfo = {}

    with open(filePath, 'r') as file:
        for line in file:
            line = line.strip()  # Remove any trailing whitespace
            if line:  # Skip empty lines
                parts = line.split(',')
                identifier = parts[0]  # Get the entire first part to identify the type

                if identifier.startswith('Level'):
                    level, height = parts[0], float(parts[1])
                    levelInfo[level] = height
                elif identifier.startswith('N'):
                    node, x, y, z = parts[0], float(parts[1]), float(parts[2]), float(parts[3])
                    nodeInfo[node] = [x, y, z]
                elif identifier.startswith('L'):
                    line, node1, node2 = parts[0], parts[1], parts[2]
                    lineInfo[line] = [node1, node2]
                elif identifier.startswith('A'):
                    area, *nodes = parts
                    areaInfo[area] = nodes
                elif identifier.startswith('W'):
                    wall, *nodes = parts
                    wallInfo[wall] = nodes

    return levelInfo, nodeInfo, lineInfo, areaInfo, wallInfo

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
        createLine(SapModel, node1[1:], node2[1:])

    # Create Floors in ETABS
    for floorName, nodesList in floorInfo.items():
        # Assuming node names are like 'N1', 'N2', etc., and converting them to integers for ETABS
        nodesList = [(node[1:]) for node in nodesList]
        createArea(SapModel, nodesList)

    # Create Floors in ETABS
    for wallName, nodesList in wallInfo.items():
        # Assuming node names are like 'N1', 'N2', etc., and converting them to integers for ETABS
        nodesList = [(node[1:]) for node in nodesList]
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

# TO DO:
def createResultsFileforViktor(SapModel):
    print("hello")

# ETABS Installation location
programPath = 'D:\Computers and Structures\ETABS 21\ETABS.exe'

# Define path of created model
modelPath = 'D:\Temp'
modelName = 'Test1'

# Location and name of data from Victor
dataFileFromVictor = 'D:\\Repo\\AECTech2023\\viktor\\structural\\testData.txt'

# Launch ETABS
SapModel = launchETABS(programPath, modelPath, modelName)

# Read data from Victor
levelInfo, nodeInfo, lineInfo, floorInfo, wallInfo = readDataFromViktor(dataFileFromVictor)

createDataInETABS(levelInfo, nodeInfo, lineInfo, floorInfo, wallInfo)

# TO DO:
# Adding Load Cases
# Adding Load Combination
# Applying Supports
# Applying loads at all levels

# Run Analysis
# Create Results file for Victor

# readDataFromVictor(dataFileFromVictor)
cleanUp()





