"""
Class used for analysing waverforms for filtering and finding extrema
"""
from math import tan, atan
#from numpy import correlate
import sys
sys.path.append('C:\\Users\\tkammerer\\AppData\\Local\\Continuum\\Anaconda2\\Lib\\site-packages')
from scipy.signal import butter, filtfilt
from scipy.stats import linregress
class Analysis():
    """
    Defines the Analysis dataset as self.values, and the master display as self.master
    """
    def __init__(self, data, master = None):
        self.master = master
        self.values = data

    """
    Finds the slope to the right of a given sample value
    """
    def differentiate(self, x):
        der = self.values[x + 1] - self.values[x]
        return der

    """
    Finds the global maximum and minimum of a dataset
    """
    def findGlobalExtrema(self):
        return self.findInvertedData(max(self.values))[0], self.findInvertedData(min(self.values))[0]

    """
    Finds all maxima and minima of a dataset
    """
    def findExtrema(self, minTest = 1, maxTest = None):
        if maxTest == None:
            maxTest = len(self.values) - 1
        maxima = list()
        minima = list()
        if maxTest <= minTest:
            return maxima, minima
        for x in range(minTest, maxTest):
            if self.differentiate(x) < 0 and self.differentiate(x-1) >= 0 or self.differentiate(x) <= 0 and self.differentiate(x-1) > 0:
                maxima.append(x)
            if self.differentiate(x) > 0 and self.differentiate(x-1) <= 0 or self.differentiate(x) >= 0 and self.differentiate(x-1) < 0:
                minima.append(x)
        return maxima, minima

    """
    For a given y-value, returns all x-values which satisfy the inverse waveform
    """
    def findInvertedData(self, resultantValue):
        xVal = list()
        for n in range(len(self.values)):
            if self.values[n] == resultantValue:
                xVal.append(n)
        return xVal

    """
    Finds the mean of the dataset between a minimum and maximum x-value
    """
    def findMean(self, minTest = 0, maxTest = None):
        if maxTest == None:
            maxTest = len(self.values)
        mean = sum(self.values[minTest:maxTest])/float(maxTest-minTest)
        return mean
    
    """
    Returns a dataset which has been vertically translated such that it's mean value is 0
    """
    def zeroShift(self):
        mean = sum(self.values)/len(self.values)
        values = list()
        for n in range(len(self.values)):
            values.append(self.values[n]-mean)
        return values
    
    """
    Finds the maximum value of a 2-dimensional array
    """
    def twoDMax(self, twoDimensionalArray):
        a = twoDimensionalArray
        maxes = list()
        for n in range(len(a)):
            maxes.append(max(a[n]))
        return max(maxes)

    """
    Note: all filters are denoted as 'apply' + filterName
    """
    
    """
    Returns the possessed dataset, translated to start when x equals 0
    """
    def applyNone(self, start, requestData = False):
        return self.values, 0, list()

    """
    Returns the dataset after it has been run through a lowpass filter
    """
    def applyLowpass(self, start, requestData = False):
        if len(self.values) <= 18:
            return [0, 0], 0, list()
        else:
            b, a = butter(5, .1, 'lowPass')
            return filtfilt(b, a, self.values), start, list()

    """
    Isolates the bottom return of a bathymetric LIDAR waveform
    """
    def applyRaw_Bottomreturn_Isolation(self, start, requestData = False):
        reduced = self.applyNoise_Reduction(0)[0]
        derivative = Analysis(reduced).applyDerivative(0)[0]
        derivative = Analysis(derivative).applyDerivative(0)[0]
        smoothDer = Analysis(derivative).applyLowpass(0)[0]
        maxima, minima = Analysis(smoothDer).findExtrema()
        minimums = [maxima[0], maxima[0]]
        for m in minima:
            if m > 250:
                break
            if self.values[m] > .01*max(self.values):
                if smoothDer[m] < smoothDer[minimums[1]]:
                    if smoothDer[m] < smoothDer[minimums[0]]:
                        minimums[1] = int(minimums[0])
                        minimums[0] = int(m)
                    else:
                        minimums[1] = int(m)
        if minimums[1] < minimums[0]:
            bottomReturn = int(minimums[0])
        else:
            bottomReturn = int(minimums[1])
        for n in range(len(maxima)):
            if maxima[n] > bottomReturn:
                break
        leading = int(maxima[n-1])
        """
        Decompress the waveform
        """
        values = Analysis(self.applyLogAmp(0)[0]).applyNoise_Reduction(0)[0]
        """
        Find the intersection point between the waveform and a 10% threshold of the bottom return
        """
        for n in range(bottomReturn, len(values)):
            if .1*values[bottomReturn] > values[n]:
                endPoint = n
                break
        """
        Create line from intersection point and minimum
        """
        clear = False
        while not clear:
            m = (values[leading]-values[endPoint])/(leading-endPoint)
            b = values[leading]-m*leading
            clear = True
            for n in range(bottomReturn, leading, -1):
                if values[n] < m*n+b:
                    leading+=1
                    clear = False
                    break
        """
        Move intersection point to closest intersection between line and waveform
        """
        for n in range(bottomReturn, endPoint):
            if values[n] < m*n+b:
                endPoint = n
                break
        """
        Highlight minimum, intersection point, and line
        """
        if self.master != None:
            self.master.addHighlightPoint(bottomReturn, self.values[bottomReturn], 'red')
            self.master.addHighlightPoint(leading, self.values[leading], 'purple')
            self.master.addHighlightPoint(endPoint, self.values[endPoint], 'pink')
        """
        Generate new values by subtracting the line from the waveform
        """
        returnValues = list()
        for x in range(leading, endPoint+1):
            returnValues.append(values[x]-(m*x+b))
        try:
            return returnValues, leading, [max(returnValues), len(returnValues), leading]
        except ValueError:
            return [0, 0], 0, [0, 0, 0]
        

    def applyBottomreturn_Isolation(self, start, requestData = False):
        derivative, s, d = self.applyDerivative(0)
        derivative, s, d = Analysis(derivative).applyDerivative(0)
        smoothDer, s, d = Analysis(derivative).applyLowpass(0)
        maxima, minima = Analysis(smoothDer).findExtrema()
        minimums = [maxima[0], maxima[0]]
        for m in minima:
            if m > 250:
                break
            if self.values[m] > .01*max(self.values):
                if smoothDer[m] < smoothDer[minimums[1]]:
                    if smoothDer[m] < smoothDer[minimums[0]]:
                        minimums[1] = int(minimums[0])
                        minimums[0] = int(m)
                    else:
                        minimums[1] = int(m)
        if minimums[1] < minimums[0]:
            bottomReturn = int(minimums[0])
        else:
            bottomReturn = int(minimums[1])
        for n in range(len(maxima)):
            if maxima[n] > bottomReturn:
                break
        starting = int(maxima[n-1])
        if self.master != None:
            self.master.addHighlightPoint(bottomReturn, self.values[bottomReturn], 'red')
        """
        Detect the leading edge
        """
        leading = int(starting)
        """
        Find the intersection point between the waveform and a 10% threshold of the bottom return
        """
        for n in range(bottomReturn, len(self.values)):
            if .1*self.values[bottomReturn] > self.values[n]:
                endPoint = n
                break
        """
        Create line from intersection point and minimum
        """
        clear = False
        while not clear:
            m = (self.values[leading]-self.values[endPoint])/(leading-endPoint)
            b = self.values[leading]-m*leading
            clear = True
            for n in range(bottomReturn, leading, -1):
                if self.values[n] < m*n+b:
                    leading+=1
                    clear = False
                    break
        """
        Move intersection point to closest intersection between line and waveform
        """
        for n in range(bottomReturn, endPoint):
            if self.values[n] < m*n+b:
                endPoint = n
                break
        """
        Highlight minimum, intersection point, and line
        """
        if self.master != None:
            self.master.addHighlightPoint(leading, self.values[leading], 'purple')
            self.master.addHighlightPoint(endPoint, self.values[endPoint], 'pink')
            self.master.addHighlightLine(0, b, -b/m, 0)
        """
        Generate new values by subtracting the line from the waveform
        """
        values = list()
        for x in range(leading, endPoint+1):
            values.append(self.values[x]-(m*x+b))
        try:
            return values, leading, [max(values), len(values), leading]
        except ValueError:
            return [0, 0], 0, [0, 0, 0]

    """
    Applies a Christmas Tree filter to the bottomreturn of a bathymetric LIDAR waveform
    """
    def applyChristmas_Tree(self, start, requestData = False):
        if len(self.values) < 6:
            return [0, 0], 0, [0, 0, 0, 0, 0, 0, 0]
        maximum, minimum = self.findGlobalExtrema()
        maxVal = self.values[maximum]
        if self.master != None:
            self.master.addHighlightPoint(maximum, maxVal, 'red')
        linePoints = [list(), list()]
        for n in range(len(self.values)):
            if self.values[n] >= .25*maxVal and self.values[n] <= .75*maxVal:
                if n < maximum:
                    linePoints[0].append([n, self.values[n]])
                else:
                    linePoints[1].append([n, self.values[n]])
        slope, intercept, r_value = [0, 0], [0, 0], [0, 0]
        if len(linePoints[0]) < 2 or len(linePoints[1]) < 2:
            return [0, 0], 0, [0, 0, 0, 0, 0, 0, 0]
        for n in range(2):
            if len(linePoints[n]) > 2:
                slope[n], intercept[n], r_value[n], p_value, std_err = linregress(linePoints[n])
            else:
                slope[n] = (linePoints[n][0][1]-linePoints[n][1][1])/(linePoints[n][0][0]-linePoints[n][1][0])
                intercept[n] = linePoints[n][0][1]-slope[n]*linePoints[n][0][0]
                r_value[n] = 1.0
        if slope[0] == slope[1]:
            return [0, 0], 0, [0, 0, 0, 0, 0, 0, 0]
        intersection = (intercept[1]-intercept[0])/(slope[0]-slope[1])
        if self.master!= None:
            self.master.addHighlightLine(linePoints[0][0][0], intercept[0]+slope[0]*linePoints[0][0][0], linePoints[1][len(linePoints[1])-1][0], intercept[0]+slope[0]*linePoints[1][len(linePoints[1])-1][0])
            self.master.addHighlightLine(linePoints[1][len(linePoints[1])-1][0], intercept[1]+slope[1]*linePoints[1][len(linePoints[1])-1][0], linePoints[0][0][0], intercept[1]+slope[1]*linePoints[0][0][0])
            for n in range(len(linePoints)):
                for m in range(len(linePoints[n])):
                    self.master.addHighlightPoint(linePoints[n][m][0], linePoints[n][m][1])
        if intersection < 0 or intersection > len(self.values):
            return [0, 0], 0, [0, 0, 0, 0, 0, 0, 0]
        for x in range(int(intersection), 0, -1):
            if intercept[0]+slope[0]*x - self.values[x] <= .01:
                startingPoint = x
                break
        for x in range(int(intersection), len(self.values)):
            if intercept[1]+slope[1]*x - self.values[x] <= .01:
                endingPoint = x
                break
        values = list()
        try:
            for x in range(startingPoint, endingPoint):
                if x < intersection:
                    values.append(intercept[0]+slope[0]*x-self.values[x])
                else:
                    values.append(intercept[1]+slope[1]*x-self.values[x])
        except UnboundLocalError:
            pass
        if len(values) <= 2:
            return [0, 0], 0, [0, 0, 0, 0, 0, 0, 0]
        if not requestData:
            return values, startingPoint+start, list()
        else:
            standard = [0,34.59591151,181.0065031,390.1960062,668.0224207,1019.288653,1447.788669,1956.362735,2546.959288,3220.701341,3977.955599,4818.402784,5591,4703.829564,3895.474605,3163.559533,2505.355592,1917.838918,1397.744873,941.618485,545.8609216,206.7719882,-3.42E-12]
            xrcov = self.xcov(standard, values)
            return values, startingPoint+start, list([max(values), len(values), xrcov, slope[0], slope[1], pow(r_value[0],2), pow(r_value[1],2)])

    """
    Determines the cross-covariance between two datasets: a and b
    """
    def xcov(self, a, b):
        a = Analysis(a).zeroShift()
        b = Analysis(b).zeroShift()
        length = 2*max([len(a), len(b)])-1
        output = list()
        for n in range(length):
            addList = list()
            for m in range(abs((length-1)/2-n)):
                addList.append(0)
            if n <= (length+1)/2:
                c = self.correlate(addList + a, b + addList)
            else:
                c = self.correlate(a + addList, addList + b)
            output.append(c)
        return self.twoDMax(output)
        
    def correlate(self, a, b):
        amean, bmean = 0, 0
        for n in a:
            amean += n
        amean /= len(a)
        for n in b:
            bmean += n
        bmean /= len(b)
        cov = 0
        for n in range(len(a)):
            cov += (a[n]-amean)*(b[n]-bmean)
        cov /= len(a)
        return cov
        

    """
    Amplifies a bathymetric LIDAR waveform from it's compressed state to original intensity reception
    """
    def applyLogAmp(self, start, requestData = False):
        if max(self.values) > 255:
            return [0, 0], 0, list()
        logAmp = [0.617,0.617,0.617,0.617,0.617,0.617,0.617,0.617,0.617,0.617,0.617,0.617,0.617,
                  0.617,0.617,0.617,0.617,0.617,0.617,0.617,0.644,0.67,0.697,0.723,0.75,0.776,
                  0.803,0.829,0.856,0.882,0.909,0.936,0.962,0.989,1.015,1.056,1.104,1.152,1.2,
                  1.248,1.296,1.344,1.393,1.441,1.489,1.537,1.585,1.633,1.681,1.741,1.813,1.885,
                  1.958,2.03,2.102,2.174,2.246,2.319,2.391,2.463,2.535,2.608,2.68,2.752,2.829,
                  2.926,3.023,3.12,3.217,3.314,3.411,3.508,3.605,3.702,3.799,3.896,3.993,4.09,
                  4.187,4.284,4.381,4.478,4.621,4.824,5.026,5.229,5.432,5.634,5.837,6.039,6.242,
                  6.445,6.647,6.85,7.053,7.255,7.469,7.712,7.956,8.199,8.442,8.685,8.928,9.171,
                  9.415,9.658,9.901,10.144,10.387,10.63,10.874,11.117,11.36,11.603,11.968,12.414,
                  12.86,13.306,13.752,14.198,14.644,15.09,15.536,15.982,16.428,16.874,17.32,17.766,
                  18.212,18.755,19.607,20.46,21.313,22.165,23.018,23.87,24.723,25.576,26.428,
                  27.281,28.133,28.986,29.89,30.925,31.961,32.997,34.032,35.068,36.103,37.139,
                  38.174,39.21,40.245,41.281,42.316,43.352,44.387,45.423,47.088,48.811,50.534,
                  52.256,53.979,55.701,57.424,59.146,60.869,62.591,64.314,66.037,67.759,69.491,
                  71.494,73.497,75.5,77.503,79.506,81.509,83.512,85.515,87.518,89.521,91.524,
                  93.527,95.53,97.533,99.536,101.982,104.897,107.811,110.725,113.64,116.554,119.469,
                  122.383,125.298,128.212,131.126,134.041,136.955,139.87,142.816,145.828,148.841,
                  151.853,154.866,157.878,160.891,163.903,166.916,169.928,172.941,175.953,178.966,
                  181.979,184.991,186.214,187.213,188.212,189.211,190.21,191.209,192.207,193.206,
                  194.205,195.204,196.203,197.202,198.201,199.2,200.198,201.1,201.814,202.528,203.242,
                  203.956,204.67,205.384,206.098,206.811,207.525,208.125,208.125,208.125,208.125,
                  208.125,208.125,208.125,208.125,208.125,208.125,208.125,208.125,208.125,208.125,208.125]
        values = list()
        for val in self.values:
            values.append(val*logAmp[int(val)])
        return values, start, list()

    """
    Attempts to reduce the background noise of a waveform
    """
    def applyNoise_Reduction(self, start, requestData = False):
        bottomMean = self.findMean(200)
        values = list()
        for n in range(len(self.values)):
            values.append(self.values[n]-bottomMean)
        return values, start, list()

    """
    Returns a dataset of the waveform's derivative over time
    """
    def applyDerivative(self, start, requestData = False):
        values = list()
        for x in range(len(self.values)-1):
            values.append(self.differentiate(x))
        return values, start+.5, list()

    def applyIncrease(self, start, requestData = False):
        values = list()
        for n in self.values:
            values.append(n+100)
        return values, start, list()