import numpy, sys, os.path,argparse
from skimage import io
from skimage.util import img_as_float
from skimage.segmentation import felzenszwalb, quickshift
from osgeo import gdal,osr,ogr


parser = argparse.ArgumentParser(prog="Grapefruit",description="Segments a image using either felzenszwalb or quickshift algorithim with the option of using a shapefile to mask. The ouput is saved as a shapefile")
parser.add_argument("-inImg", help="this should be the path of the img to be segmented",required=True)
parser.add_argument("-outDir", help="this should be the path of the output dir",required=True)
parser.add_argument("-outName", help="this should be the name of the output file",required=True)
parser.add_argument("-segType", type=int, help = "1 = felzenszwalb, 2 = quickshift", required=True)
parser.add_argument("-maskShp", help="this should be the the path of the mask shapefile if one is to be used")
parser.add_argument("-minSize", type=int, help = "a integer for the minimum pixel size", required=True)
parser.add_argument("-sigma", type=float, help = "a float for the sigma", required=True)
parser.add_argument("-fScale", type=float, help = "a float for felzenszwalb scale param")
parser.add_argument("-fMulti", type=bool, help = "a boolean for felzenszwalb multichannelbool param")
parser.add_argument("-qRatio", type=float, help = "a float for quickshift ratio param between 0 and 1")
parser.add_argument("-qKSize", type=float, help = "a float for quickshift kernel_size param")
parser.add_argument("-qMaxD", type=float, help = "a float for quickshift max_dist param")
parser.add_argument("-qConToLab", type=bool, help = "a boolean for quickshift convert2lab param")
parser.add_argument("-qRNG", type=int, help = "a integer for quickshift random_seed param")
args = parser.parse_args()

def writeSegmentsToShapefile(segments,rasterInputPath,minSize,outputFilePath):
	#open raster
	raster=gdal.Open(rasterInputPath)
	#create a temp raster dataset to use for output array
	tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', raster, 0)
	#create a band for polygonize
	#copy band from temp data
	outBand=tmp_ds.GetRasterBand(1)
	#repalce band array with segments array
	outBand.WriteArray(segments)
	#drop small parts
	gdal.SieveFilter(outBand, None, outBand, minSize)

	#setup shp file ready for polygonize
	#get shpfile driver
	driver = ogr.GetDriverByName("ESRI Shapefile")
	#get projection from temp data
	srs = osr.SpatialReference()
	srs.ImportFromWkt( raster.GetProjectionRef() )
	#create empty shp file
	outDatasource = driver.CreateDataSource(outputFilePath) 
	#create empty layer with projection in shp file     
	outLayer = outDatasource.CreateLayer(outputFilePath,srs)
	#add a field
	newField = ogr.FieldDefn('Class', ogr.OFTInteger)
	outLayer.CreateField(newField)

	#Polygonize
	#populate empty layer by polgonize the band with the segments array
	gdal.Polygonize(outBand, None,outLayer, 0,[],callback=None) 
	#drop the shp file from memory so it can be used
	outDatasource.Destroy()

def getMaskArray(rasterInputPath,maskShpFilePath):
	#open raster
	raster=gdal.Open(rasterInputPath)

	#open shapefile
	shape_dataset = ogr.Open(maskShpFilePath)
	#get layer
	shape_layer = shape_dataset.GetLayer()
	source = shape_layer.GetSpatialRef()
	
	#temp dataset for mask raster
	mask_ds = gdal.GetDriverByName('MEM').CreateCopy('', raster, 0)
	mask_ds.SetGeoTransform(raster.GetGeoTransform())
	mask_ds.SetProjection(source.ExportToWkt())
	
	
	#temp band for mask
	mem_band = mask_ds.GetRasterBand(1)
	#fill with 0
	mem_band.Fill(0)
	#change not data to 0, shape will be rows,cols B
	mem_band.SetNoDataValue(0)

	
	#rasterize vector data to putsh to, band index, layer to rasterize
	gdal.RasterizeLayer(mask_ds,[1],shape_layer,None,None,[1],['ALL_TOUCHED=TRUE'])
	return mem_band.ReadAsArray()

def getArrayToSegment(rasterInputPath,maskShpFilePath):
	#open raster
	raster=gdal.Open(rasterInputPath)
	rasterArray=raster.ReadAsArray()
	#change 0 to next to 0
	rasterArray = numpy.where(rasterArray==0, 0.000001, rasterArray) 
	#turn nan to -1
	rasterArray=numpy.nan_to_num(rasterArray)
	rasterArray = numpy.where(rasterArray==0, -1, rasterArray) 
	#use mask to zero out unwnated parts
	if maskShpFilePath is not None:
		rasterArray=numpy.multiply(rasterArray, getMaskArray(rasterInputPath,maskShpFilePath))
	#reshape array for skimage
	arrayToSegment=numpy.transpose(rasterArray,(1,2,0))
	arrayToSegment = numpy.nan_to_num(arrayToSegment)
	return arrayToSegment

def runFelzenszwalb():
	inputValidation = True
	if args.fScale is None:
		inputValidation = False
		print("fScale requires a value for felzenszwalb")
	if args.fMulti is None:
		inputValidation = False
		print("fMulti requires a value for felzenszwalb")
	if inputValidation == False:
		exit()
	#get array from image to segment
	arrayToSegment = getArrayToSegment(args.inImg,args.maskShp)
	#use felzenszwalb to create segment array
	segments=felzenszwalb(arrayToSegment, scale=args.fScale, sigma=args.sigma, min_size=args.minSize,multichannel=args.fMulti)
	#use mask to zero out unwnated parts
	if args.maskShp is not None:
		segments=numpy.multiply(segments, getMaskArray(args.inImg,args.maskShp))
	#write out to shpfile
	writeSegmentsToShapefile(segments, args.inImg, args.minSize, args.outDir + "\\" + args.outName + ".shp")

def runQuickshift():
	inputValidation = True
	if args.qRatio is None:
		inputValidation = False
		print("qRatio requires a value for quickshift")
	if args.qKSize is None:
		inputValidation = False
		print("qKSize requires a value for quickshift")
	if args.qMaxD is None:
		inputValidation = False
		print("qMaxD requires a value for quickshift")
	if args.qConToLab is None:
		inputValidation = False
		print("qConToLab requires a value for quickshift")
	if args.qRNG is None:
		inputValidation = False
		print("qRNG requires a value for quickshift")		
	if inputValidation == False:
		exit()
	#get array from image to segment
	arrayToSegment = getArrayToSegment(args.inImg,args.maskShp)
	#use quickshift to create segment array
	segments=quickshift(arrayToSegment, ratio=args.qRatio, kernel_size=args.qKSize, max_dist=args.qMaxD, return_tree=False, sigma=args.sigma, convert2lab=args.qConToLab, random_seed=args.qRNG)
	#use mask to zero out unwnated parts
	if args.maskShp is not None:
		segments=numpy.multiply(segments, getMaskArray(args.inImg,args.maskShp))
	#write out to shpfile
	writeSegmentsToShapefile(segments, args.inImg, args.minSize, args.outDir + "\\" + args.outName + ".shp")

if __name__ == "__main__":

	#validate some inputs exist
	inputValidation = True
	#check inImg is a valid file
	if os.path.isfile(args.inImg) == False or os.path.exists(args.inImg) == False:
		inputValidation = False
		print("inImg should be a input image that exists")
	#check outDir is a valid dir and exists
	if os.path.isdir(args.outDir) == False or os.path.exists(args.outDir) == False:
		inputValidation = False
		print("outDir should be a output dir that exists")
	#if maskShp is entered make sure it is a vlaid file that exists
	if args.maskShp is not None:
		if os.path.isfile(args.maskShp) == False or os.path.exists(args.maskShp) == False:
			inputValidation = False
			print("maskShp should be a mask shp file that exists")
	#if inputValidation falied exit
	if inputValidation == False:
		exit()
		
	#if intial validation passed run seg depending on type
	if args.segType==1:
		runFelzenszwalb()
	elif args.segType==2:
		runQuickshift()
	else:
		print("oh noes wrong value input for segType")