<b>Prerequisites</b><br>
            Python<br>
 GDAL for python<br>
 Python libaries numpy and scikit-image<br>
<br>
<br>
<b>Parameters</b><br>
<br>
Required<br>
-inImg, this should be the path of the img to be segmented<br>
-outDir, this should be the path of the output dir<br>
-outName, this should be the name of the output file<br>
-segType, 1 = felzenszwalb, 2 = quickshift<br>
-minSize, a integer for the minimum pixel size<br>
-sigma, a float for the sigma<br>
<br>
Required for felzenszwalb<br>
-fScale, a float for felzenszwalb scale param<br>
-fMulti, a boolean for felzenszwalb multichannelbool param<br>
<br>
Required for quickshift<br>
-qRatio, a float for quickshift ratio param between 0 and 1<br>
-qKSize, a float for quickshift kernel_size param<br>
-qMaxD, a float for quickshift max_dist param<br>
-qConToLab, a boolean for quickshift convert2lab param<br>
-qRNG, a integer for quickshift random_seed param<br>
<br>
Optional<br>
-maskShp, this should be the the path of the mask shapefile if one is to be used

