#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:10:21 2020

@author: jaymz
"""

import numpy as np

wavelength = None

#-------------Element Definitions-----------------
def lens(focalLength):
    return np.matrix([[1,0],[-1.0/focalLength,1]])
def propagate(distance):
    return np.matrix([[1,distance],[0,1]])
def mirror(radiusCurv):
    return np.matrix([[1,0],[-2.0/radiusCurv,1]])
def flatInterface(n1,n2):
    return np.matrix([ [1.0,0.0] , [0,n1/n2] ])
def curvedInterface(n1,n2,R):
    return np.matrix([ [1.0,0.0] , [(n1-n2)/(R*n2), n1/n2] ])

def transferQ(qi,matrix):
    return (qi*matrix[0,0] + matrix[0,1])/(qi*matrix[1,0]+matrix[1,1])
def width(complexQ):
    return np.sqrt(-wavelength/(np.pi*np.imag(1.0/complexQ)))
def widthSlope(complexQ):
    return wavelength/np.pi/np.imag(complexQ)*np.real(complexQ)/width(complexQ)
def radiusRecip(complexQ):
    return np.real(1.0/complexQ)