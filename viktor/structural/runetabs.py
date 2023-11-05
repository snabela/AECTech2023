import os
import sys
import comtypes.client
import json
from scipy.spatial import ConvexHull
import numpy as np

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
    columnInfo = {}
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
        nodes = [int(node_number) + 1 for node_number in beam_nodes]  # Adjust node numbering
        # Retrieve the z-coordinates for the nodes that make up the beam
        node_z_coords = [nodeInfo[node][2] for node in nodes]
        # Beams should have the same z-coordinate
        if node_z_coords.count(node_z_coords[0]) == len(node_z_coords):
            beamInfo[beam_counter] = nodes
        else:
            print(f"Beam {beam_counter} uses nodes {nodes} at different z levels, which is unusual for a beam.")
        beam_counter += 1

    # Process columns (assuming each entry in columns is a list of node numbers for that column)
    column_counter = 1
    for column_nodes in data['columns']:
        nodes = [int(node_number) + 1 for node_number in column_nodes]  # Adjust node numbering
        # Retrieve the z-coordinates for the nodes that make up the column
        node_z_coords = [nodeInfo[node][2] for node in nodes]
        # Columns should have different z-coordinates
        if node_z_coords[0] != node_z_coords[1]:
            columnInfo[column_counter] = nodes
        else:
            print(f"Column {column_counter} uses nodes {nodes} at the same z level, which is unusual for a column.")
        column_counter += 1

    # # Process floors (assuming each entry in floors is a list of node numbers for that floor)
    # floor_counter = 1
    # for floor_nodes in data['floors']:
    #     nodes = [int(node_number) + 1 for node_number in floor_nodes]  # Adjust node numbering
    #     # Check if any node's z-coordinate is 0, skip the floor
    #     if any(nodeInfo[node][2] == 0 for node in nodes):
    #         continue
    #     # Check if all z-coordinates are the same for the floor
    #     if len(set(nodeInfo[node][2] for node in nodes)) != 1:
    #         print(f"Warning: Floor {floor_counter} has nodes at different z levels.")
    #     # Check if the number of nodes is less than 3 or more than 4
    #     if not 3 <= len(nodes) <= 4:
    #         print(f"Warning: Floor {floor_counter} has an invalid number of nodes: {len(nodes)}.")
    #     floorInfo[floor_counter] = nodes
    #     floor_counter += 1
    
    # Group nodes by elevation
    elevation_groups = {}
    for node_id, (x, y, z) in nodeInfo.items():
        elevation_groups.setdefault(z, []).append((x, y, node_id))

    # Process each elevation group to find floor plates
    floor_counter = 1
    for z, nodes in elevation_groups.items():
        if z == 0:  # Skip the base level at z=0
            continue
        points = np.array([(x, y) for x, y, node_id in nodes])
        hull = ConvexHull(points)
        hull_points = hull.vertices

        # Sort hull points in clockwise order
        center = np.mean(points[hull_points], axis=0)
        angles = np.arctan2(points[hull_points, 1] - center[1], points[hull_points, 0] - center[0])
        hull_points = hull_points[np.argsort(-angles)]

        # Map back to node ids
        ordered_node_ids = [nodes[i][2] for i in hull_points]
        floorInfo[floor_counter] = ordered_node_ids
        floor_counter += 1

    # Infer levels from the unique z values (excluding the base level at z=0)
    z_values = sorted({coord[2] for coord in nodeInfo.values() if coord[2] > 0})
    levelInfo = {f"Level{i+1}": round(z, 3) for i, z in enumerate(z_values)}

    return nodeInfo, beamInfo, columnInfo, floorInfo, levelInfo

# Create all data in ETABS
def createDataInETABS(nodeInfo, beamInfo, columnInfo, floorInfo, levelInfo):
    # Create Levels in ETABS
    levelNames = list(levelInfo.keys())
    levelElevations = list(levelInfo.values())
    createLevels(SapModel, levelNames, levelElevations)

    # Create Nodes in ETABS
    for nodeName, coords in nodeInfo.items():
        x, y, z = coords
        createNode(SapModel, x, y, z)
    
    SapModel.View.RefreshView()

    # Create beams in ETABS
    for lineName, nodes in beamInfo.items():
        node1, node2 = nodes
        createLine(SapModel, node1, node2)
    
    SapModel.View.RefreshView()
    
    # Create columns in ETABS
    for lineName, nodes in columnInfo.items():
        node1, node2 = nodes
        createLine(SapModel, node1, node2)
    
    SapModel.View.RefreshView()

    # Create Areas (Floors) in ETABS
    for floorName, nodesList in floorInfo.items():
        createArea(SapModel, nodesList)
    
    SapModel.View.RefreshView()

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
    ret = SapModel.FrameObj.AddByPoint(str(node1), str(node2), Name)

# Create area in ETABS
def createArea(SapModel, nodesList):
    # Convert each integer node number in nodesList to a string
    nodesListAsString = [str(node) for node in nodesList]
    ret = SapModel.AreaObj.AddByPoint(len(nodesList), nodesListAsString, '')

# Spit out data for Viktor
def createResultsFileforViktor(SapModel):
    print("hello")

# ETABS Installation location
programPath = 'D:\Computers and Structures\ETABS 21\ETABS.exe'

# Location and name of data from Victor
dataFileFromVictor = 'D:\\Repo\\AECTech2023\\viktor\\structural\\building_structure.json'

# Read data from Victor
nodeInfo, beamInfo, columnInfo, floorInfo, levelInfo = process_building_structure(dataFileFromVictor)

# Launch ETABS
SapModel = launchETABS(programPath, 'D:\\Repo\\AECTech2023\\viktor\\structural\\analysismodel', 'Template')

createDataInETABS(nodeInfo, beamInfo, columnInfo, floorInfo, levelInfo)

# TO DO:
# Applying Supports
# Applying loads at all levels

# Run Analysis
# Create Results file for Victor

# readDataFromVictor(dataFileFromVictor)
cleanUp()





