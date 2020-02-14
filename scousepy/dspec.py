import numpy as np
from astropy.convolution import convolve, Gaussian1DKernel, Box1DKernel

class DSpec(object):
    def __init__(self,x,y,noise,SNR=3,kernelsize=3,method='gauss'):
        """

        """
        self.x = x
        self.y = y
        self.noise = noise

        self.kernelsize = kernelsize
        self.SNR = SNR
        self.kernel = get_kernel(self, method=method)
        self.ysmooth = convolvespec(self)

        self.d1 = compute_gradient(self.ysmooth, self.x[1]-self.x[0])
        self.d2 = compute_gradient(self.d1, self.x[1]-self.x[0])
        self.d3 = compute_gradient(self.d2, self.x[1]-self.x[0])
        self.d4 = compute_gradient(self.d3, self.x[1]-self.x[0])

        self.conditionmask,self.ncomps = get_components(self)
        self.peaks = get_peaks(self)
        self.centroids = get_centroids(self)
        self.widths = get_widths(self)
        self.guesses = get_guesses(self)

        self.conditionmask_n,self.ncomps_n = get_components(self, positives=False)
        self.peaks_n = get_peaks(self, positives=False)
        self.centroids_n = get_centroids(self, positives=False)
        self.widths_n = get_widths(self, positives=False)
        self.guesses_n = get_guesses(self, positives=False)

def get_kernel(self, method='gauss'):
    if method=='gauss':
        return Gaussian1DKernel(self.kernelsize)
    elif method=='box':
        return Box1DKernel(self.kernelsize)
    else:
        raise ValueError("Method not recognised. Please use method='gauss' or method='box' ")

def convolvespec(self,):
    return convolve(self.y, self.kernel)

def compute_gradient(y,inc):
    """
    may need to trim the edges
    """
    return np.gradient(y)/inc

def get_components(self, positives=True):
    """

    """
    # value must be greater than SNR*rms
    condition1=np.array(self.y>(self.SNR*self.noise), dtype='int')[1:]
    if positives:
        # second derivative must be negative
        condition2=np.array(self.d2[1:]<0, dtype='int')
    else:
        condition2=np.array(self.d2[1:]>0, dtype='int')
    if positives:
        # fourth derivative must be positive
        condition3=np.array(self.d4[1:]>0, dtype='int')
    else:
        condition3=np.array(self.d4[1:]<0, dtype='int')
    # third derivative must be close to zero
    condition4=np.array(np.abs(np.diff(np.sign(self.d3)))!=0, dtype='int')

    # put all conditions together in a single mask
    conditionmask=condition1*condition2*condition3*condition4

    # find number of peaks
    ncomps=np.size(np.where(conditionmask))

    return conditionmask, ncomps

def get_peaks(self, positives=True):
    if positives:
        id = np.array(np.where(self.conditionmask)).ravel()
    else:
        id = np.array(np.where(self.conditionmask_n)).ravel()
    return self.y[id]

def get_centroids(self, positives=True):
    if positives:
        id = np.array(np.where(self.conditionmask)).ravel()
    else:
        id = np.array(np.where(self.conditionmask_n)).ravel()
    return self.x[id]

def get_widths(self, positives=True):
    if positives:
        id = np.array(np.where(self.conditionmask)).ravel()
    else:
        id = np.array(np.where(self.conditionmask_n)).ravel()
    inflection = np.abs(np.diff(np.sign(self.d2)))
    widths = np.sqrt(np.abs(self.y/self.d2)[id])
    return widths

def get_guesses(self, positives=True):
    guesses=[]
    if positives:
        for i in range(self.ncomps):
            guesses.append(self.peaks[i])
            guesses.append(self.centroids[i])
            guesses.append(self.widths[i])
    else:
        for i in range(self.ncomps_n):
            guesses.append(self.peaks_n[i])
            guesses.append(self.centroids_n[i])
            guesses.append(self.widths_n[i])

    return guesses
