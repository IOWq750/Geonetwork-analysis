import arcpy
from arcpy.sa import *
import os


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "RiverNetworkDevelopment"
        self.alias = "River Network Development"

        # List of tool classes associated with this toolbox
        self.tools = [DenudationCycle, ComputeCEI]


class DenudationCycle(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Denudation Cycle"
        self.description = "Denudation Cycle"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        # Input DEM
        in_dem = arcpy.Parameter(
            displayName="DEM",
            name="in_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Input overland flow (precipitation minus evapotranspiration)
        in_overland_flow = arcpy.Parameter(
            displayName="Overland flow thickness layer (mm)",
            name="in_precip",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Input critical \tau value
        CEI_crit = arcpy.Parameter(
            displayName="Threshold CEI value",
            name="CEI_crit",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        CEI_crit.value = 40.0

        # Input coefficient a 
        coeff_a = arcpy.Parameter(
            displayName="Coefficient 'a'",
            name="a",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        coeff_a.value = 1.0

        # number of iterations
        n_iterations = arcpy.Parameter(
            displayName="Number of iterations",
            name="n_iterations",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        
        # Output DEM
        out_DEM = arcpy.Parameter(
            displayName="Output DEM",
            name="out_DEM",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Output")

        parameters = [in_dem, in_overland_flow, CEI_crit, coeff_a, n_iterations, out_DEM]
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Parameters
        inDEM = parameters[0].valueAsText
        in_overland_flow = parameters[1].valueAsText
        CEI_crit = parameters[2].valueAsText
        coeff_a = parameters[3].valueAsText
        n = int(parameters[4].valueAsText)
        out_dem = parameters[5].valueAsText
        
        # Processing
        arcpy.AddMessage('Start script')
        workdir = os.path.dirname(os.path.abspath(__file__))
        
        try:
            arcpy.CreateFileGDB_management(workdir, "processing.gdb")
        except:
            arcpy.AddMessage("'processing.gdb' already exists")
        try:
            arcpy.CreateFileGDB_management(workdir, "scratch.gdb")
        except:
            arcpy.AddMessage("'scratch.gdb' already exists")

        arcpy.env.overwriteOutput = True

        arcpy.env.extent = inDEM
        arcpy.env.snapRaster = inDEM
        arcpy.env.cellSize = inDEM
        cell_x = arcpy.GetRasterProperties_management(inDEM, "CELLSIZEX").getOutput(0)
        cell_y = arcpy.GetRasterProperties_management(inDEM, "CELLSIZEY").getOutput(0)
        cell_area = float(cell_x) * float(cell_y) / (10**6)  # cell area in sq. km

        # Create constant tau_crit raster
        outCEIcrit = CreateConstantRaster(CEI_crit, "FLOAT")
        outCEIcrit.save(workdir + "/processing.gdb/CEI_crit")
        outCoeffA = CreateConstantRaster(coeff_a, "FLOAT")
        outCoeffA.save(workdir + "/processing.gdb/Coeff_a")

        # Preprocessing
        arcpy.CopyRaster_management(inDEM, out_dem)

        for i in range(0, n):
            
            arcpy.AddMessage('Processing cycle: %s' % (i+1))  # Message to display in  the terminal
            
            # Computing slope
            outSlope0 = Slope(out_dem, "PERCENT_RISE")  # Computing slope as percent
            constant = 0.01
            outSlope = Times(outSlope0, constant)  # Computing slope as a part of 1
            
            # DEM Hydro-processing
            outFill = Fill(out_dem)  # Filling in sinks
            outFlowDir = FlowDirection(outFill)  # Computing flow directions
            # Computing flow accumulation
            # outFlowDir is flow direcitons from above
            # in_overland_flow is a runoff layer (precipitation minus evapotranspiration, measured in mm)
            outFlowAcc0 = FlowAccumulation(outFlowDir, in_overland_flow)   # Flow accumulation in mm of layer
            #outFlowAcc0.save("processing.gdb/flowacc0")
            outFlowAcc = Times(outFlowAcc0, cell_area)  # Flow accumulation in mm/sq.km
            #outFlowAcc0.save("processing.gdb/flowacc0")
            # Multiplying Slope and FlowAcc, obtaining CEI (tau)
            outCEI = Times(outSlope, outFlowAcc)
            #outTau.save('processing.gdb/tau_fact')
            # applying conversion coefficient (a)
            outCEIa = Times(outCEI, outCoeffA)  # final CEI value
            # Subtract critical CEI value (outCEIcrit) from obtained CEI value (outCEIa)
            outDenudationMM = Minus(outCEIa, outCEIcrit)  # denudation raster
            # convert to meters
            constant = 0.001
            outDenudationM = Times(outDenudationMM, constant)
            # convert negative values to zero
            constant = 0
            outDenudation = Con(outDenudationM, outDenudationM, constant, "VALUE > 0")
            #outDenudation.save(workdir  + 'scratch.gdb/denudation%s' % i)
            # Extraction
            arcpy.CopyRaster_management(out_dem, workdir + '/scratch.gdb/oldDEM')
            newDEM = Minus(workdir + '/scratch.gdb/oldDEM', outDenudation)
            newDEM.save(out_dem)
        
        return


class ComputeCEI(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Compute CEI"
        self.description = "Compute CEI"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        # Input DEM
        in_dem = arcpy.Parameter(
            displayName="DEM",
            name="in_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        # Input overland flow (precipitation minus evapotranspiration)
        in_overland_flow = arcpy.Parameter(
            displayName="Overland flow thickness layer (mm)",
            name="in_precip",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
     
        # Output tau raster
        out_tau = arcpy.Parameter(
            displayName="Output tau raster",
            name="out_tau",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Output")

        parameters = [in_dem, in_overland_flow, out_tau]
        return parameters

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        # Parameters
        inDEM = parameters[0].valueAsText
        in_overland_flow = parameters[1].valueAsText
        out_tau = parameters[2].valueAsText
        
        arcpy.AddMessage('Start script')
        workdir = os.path.dirname(os.path.abspath(__file__))
        
        try:
            arcpy.CreateFileGDB_management(workdir, "processing.gdb")
        except:
            arcpy.AddMessage("'processing.gdb' already exists")
        try:
            arcpy.CreateFileGDB_management(workdir, "scratch.gdb")
        except:
            arcpy.AddMessage("'scratch.gdb' already exists")

        arcpy.env.overwriteOutput = True

        arcpy.env.extent = inDEM
        arcpy.env.snapRaster = inDEM
        arcpy.env.cellSize = inDEM
        cell_x = arcpy.GetRasterProperties_management(inDEM, "CELLSIZEX").getOutput(0)
        cell_y = arcpy.GetRasterProperties_management(inDEM, "CELLSIZEY").getOutput(0)
        cell_area = float(cell_x) * float(cell_y) / (10**6)

        # Preprocessing
        out_dem = 'scratch.gdb/out_dem'
        arcpy.CopyRaster_management(inDEM, out_dem)

        # Computing slope
        outSlope0 = Slope(out_dem, "PERCENT_RISE")
        constant = 0.01
        outSlope = Times(outSlope0, constant)
        # Filling in sinks
        outFill = Fill(out_dem)
        # Computing flow directions
        outFlowDir = FlowDirection(outFill)
        # Computing flow accumulation
        outFlowAcc0 = FlowAccumulation(outFlowDir, in_overland_flow)
        #outFlowAcc0.save("processing.gdb/flowacc0")
        outFlowAcc = Times(outFlowAcc0,cell_area)
        #outFlowAcc.save("processing.gdb/flowacc1")
        # Multiplying Slope and FlowAcc, obtaining CEI (tau)
        outTau = Times(outSlope, outFlowAcc)
        outTau.save(out_tau)
        # Delete temporary file(s)
        arcpy.Delete_management(out_dem)
        
        return
