#! /usr/bin/env python3

import os.path
import math
import argparse
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import erf


class VsmAnalyzer:
    def __init__(self, sample):
        self.sample = sample
        self.model = 'linear'
        return None


    def analyzeData(self):
        self.analyzeHardData()
        self.analyzeEasyData()
        return None

    
    def analyzeHardData(self):
        try:
            bfup, bfdn, hparams = analyze(self.sample.data, 'hard')
            self.sample.results['hard ms'] = hparams
            self.sample.results['hk'] = hparams[1]
            self.sample.data['hard fit up']['M'] = bfup
            self.sample.data['hard fit down']['M'] = bfdn
            hup = self.sample.data['hard data up']['H']
            self.sample.data['hard fit up']['H'] = hup
            hdn = self.sample.data['hard data down']['H']
            self.sample.data['hard fit down']['H'] = hdn
        except Exception as e:
            print('Caught exception during hard axis analysis.')
            print(e)
        return None


    def analyzeEasyData(self):
        try:
            bfup, bfdn, hparams = analyze(self.sample.data, 'easy')
            self.sample.results['ms'] = hparams[0]
            self.sample.results['hc'] = hparams[1]
            self.sample.results['mr'] = hparams[2]
            self.sample.results['sqr'] = hparams[3]
            self.sample.data['easy fit up']['M'] = bfup
            self.sample.data['easy fit down']['M'] = bfdn
            hup = self.sample.data['easy data up']['H']
            self.sample.data['easy fit up']['H'] = hup
            hdn = self.sample.data['easy data down']['H']
            self.sample.data['easy fit down']['H'] = hdn
        except Exception as e:
            print('Caught exception during easy axis analysis.')
            print(e)
        return None

def analyze(data, axis):
    hup = data[axis+' data up']['H']
    mup = data[axis+' data up']['M']
    hdn = data[axis+' data down']['H']
    mdn = data[axis+' data down']['M']
    rh = 1.0
    ms_est = getms(hup, mup, hdn, mdn)
    hk_est = gethk(hup, mup, hdn, mdn, rh)
    bestpup, bestcovup = curve_fit(switchmdl, hup, mup,
        p0=[ms_est, 0, hk_est, 0])
    bestpdn, bestcovdn = curve_fit(switchmdl, hdn, mdn,
        p0=[ms_est, 0, hk_est, 0])
    ms = (bestpup[0] + bestpdn[0] ) / 2
    hk = (bestpup[2] + bestpdn[2] ) / 2
    hc = abs(bestpup[1] - bestpdn[1]) / 2
    bfup = switchmdl(hup,*bestpup)
    bfdn = switchmdl(hdn,*bestpdn)
    mr = getmr(hup, mup, hdn, mdn)
    sqr = mr / ms
    if axis == 'easy':
        return bfup, bfdn, [ms, hc, mr, sqr]
    else:
        return bfup, bfdn, [ms, hk]


def getms(hup, mup, hdn, mdn):
    a = 0.25*(ms1d(mup) + ms1d(np.flipud(mup))
              + ms1d(mdn) + ms1d(np.flipud(mdn)))
    return a


def getsigma(hup, mup, hdn, mdn):
    ms = getms(hup, mup, hdn, mdn)
    a = []
    for i in range(25):
        a.append(abs(mup[i])-abs(ms))
        a.append(abs(mdn[i])-abs(ms))
    return np.std(a)


def ms1d(m):
    mflat = []
    m0 = m[0]
    for mk in m:
        if abs((mk-m0)/m0) < 0.1:
            mflat.append(mk)
    return abs(np.mean(mflat))


def getmr(hup, mup, hdn, mdn):
    mrup = abs(mr1d(hup, mup))
    mrdn = abs(mr1d(hdn, mdn))
    mr = 0.5*(mrup+mrdn)
    return mr


def mr1d(h, m):
    mr = zerocross(m, h) 
    return mr


def gethc(hup, mup, hdn, mdn):
    zcup = zerocross(hup, mup)
    zcdn = zerocross(hdn, mdn)
    return 0.5*(abs(zcup)+abs(zcdn))


def gethk(hup, mup, hdn, mdn, rh):
    zcup = zerocross(hup, mup)
    zcdn = zerocross(hdn, mdn)
    ms = getms(hup, mup, hdn, mdn)
    hkup, slopeup = hk1d(hup, mup, rh, ms)
    hkdn, slopedn = hk1d(hdn, mdn, rh, ms)
    slopeav = 0.5*(slopeup+slopedn)
    hk = 0.5*(abs(hkup) + abs(hkdn))
    hplt = np.linspace(-hk, hk, 100)
    mplt = slopeav*hplt
    #return hplt, mplt, hk
    return hk


def hk1d(h, m, rh, ms):
    hzc = zerocross(h,m)
    h0 = h - hzc
    hlin, mlin = constrict(h0, m, rh)
    slope = np.mean(nderiv(hlin, mlin))
    hk = ms/slope
    return hk, slope


def constrict(x,y,rad):
    rx = []
    ry = []
    for xk, yk in zip(x,y):
        if abs(xk) < rad:
            rx.append(xk)
            ry.append(yk)
    return rx, ry


def centerh(hup, mup, hdn, mdn):
    zcup = zerocross(hup, mup)
    zcdn = zerocross(hdn, mdn)
    hoffs = 0.5*(zcup + zcdn)
    hups = np.array(hup) - hoffs
    hdns = np.array(hdn) - hoffs
    return hups, hdns


def nderiv(x, y):
    dydx = []
    dydx.append(0)
    ykm1 = 0
    for k in range(1,len(y)):
        dx = x[k]-x[k-1]
        if dx != 0:
            dydx.append((y[k]-y[k-1])/dx)
        else:
            dydx.append(0)
    return dydx
            

def zerocross(x, y):
    ykm1 = y[0]
    for k, yk in enumerate(y):
        if yk*ykm1 <= 0:
            m = (y[k]-y[k-1])/(x[k]-x[k-1])
            return x[k-1]-y[k-1]/m
        ykm1 = yk
    return -1


def switchmdl(h, ms, hsw, hk, moffs):
    #return moffs + ms * erf((h - hsw) / hk)
    return np.piecewise(h, 
        [h-hsw < -hk, abs(h-hsw) <= hk, h - hsw > hk],
        [-ms + moffs,
         lambda h: moffs+ms*(h-hsw)/hk,
         ms + moffs])


credits = r"""
          ____   ________
         / _  | |  _____ \
        / / | | | |     | |
       / /  | | | |     | |
      / /   | | | |     | |
     / /_  _| | | |     | |
    / __/ /_| | | |     | |
   / /      | | | |     | |
  /_/       |_| |_|     | |
 _______________________/ |
/________________________/

A Newman Group Magnetics Utility 
written by Alex Devonport.
"""

# If you improve this program, put your name in the credit string
# and claim your infinitesimal modicum of everlasting fame!

