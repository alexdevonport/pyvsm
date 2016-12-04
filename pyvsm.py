#! /usr/bin/env python3
"""
pyvsm: VSM analysis program. takes in VSM data file,
calculates Ms, Hc and Hk. Written with the promise of
returning to the Haskell version at some point.

"""

import argparse
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    parser = mkparser()
    args = parser.parse_args()
    easyax = getaxis(args)
    for fp in args.files:
        h, m = getdata(fp)
        if args.negate:
            m *= -1
        hup, mup, hdn, mdn = splitupdn(h,m)
        hup, hdn = centerh(hup, mup, hdn, mdn)
        if easyax:
            analyze_easy(hup, mup, hdn, mdn, fp, args.plot)
        else:
            analyze_hard(hup, mup, hdn, mdn, fp, 
                args.hk_radius, args.plot)
    return None


def getaxis(args):
    easy = args.easy
    hard = args.hard
    if easy != hard:  # that is, if exactly one flag were raised
        return easy or (not hard)
    else:  # if neither or both flags were raised, disambiguate
        i = str(input('Easy or hard axis data? (E/h) '))
        if 'h' in i.lower():
            return False
        else:
            return True


def analyze_hard(hup, mup, hdn, mdn, fp, rh, mkplt=True):
    hplt, mplt, hk= gethk(hup, mup, hdn, mdn, rh)
    ms = getms(hup, mup, hdn, mdn)
    hc = gethc(hup, mup, hdn, mdn)
    print('file={:s}, ms={:.4g}, hk={:.4g}'.format(fp, ms, hk))
    if mkplt:
        plot_hard(hup, mup, hdn, mdn, hplt, mplt, fp)
    return None


def plot_hard(hup, mup, hdn, mdn, hplt, mplt, fp):
    plt.plot(hup, mup, 'g', label='M-H loop data')
    plt.plot(hdn, mdn, 'g')
    plt.plot(hplt, mplt, label='hk extrapolation')
    plt.legend()
    plt.grid(True)
    plt.show()
    return None


def analyze_easy(hup, mup, hdn, mdn, fp, mkplt=True):
    ms = getms(hup, mup, hdn, mdn)
    hc = gethc(hup, mup, hdn, mdn)
    print('file={:s}, ms={:.4g}, hc={:.4g}'.format(fp, ms, hc))
    if mkplt:
        plot_easy(hup, mup, hdn, mdn, fp, ms, hc)
    return None


def plot_easy(hup, mup, hdn, mdn, fp, ms, hc):
    plt.plot(hup, mup, 'g', label='M-H loop data')
    plt.plot(hdn, mdn, 'g')
    plt.plot([-hc, -hc],[-ms, ms], [hc, hc], [-ms, ms],
        label='coercivity')
    plt.legend()
    plt.grid(True)
    plt.show()
    return None


def mkparser():
    desc = """
Analyze VSM hysteresis loops to calculate saturation magnetization (Ms),
coercivity (Hc), anisotropy field (Hk), remanent magnetization (Mr), and
squareness.
    """
    epi = """If neither -e or -r is specified, the user will be queried
as to whether the data is easy-axis or hard axis. Once easy or hard axis
is specified, all loop data files are analyzed with that option.

Calculation results are sent to stdout as a string of name-value
pairs, e.g. \"ms=5.0e-5, hk=4.03, mr=2.5e-5\".

"""
    p = argparse.ArgumentParser(description=desc, epilog=epi,
        formatter_class=argparse.RawDescriptionHelpFormatter,)
    p.add_argument('files', type=str, metavar='FILE', nargs='+',
    help="""hysteresis loop data file.
Data should be stored as two tab-delimited colums, containing field
data and moment data, preceded by a seven-row header.""")
    p.add_argument('-e','--easy', action='store_true',
        help="""Indicate that loop(s) are easy-axis loops. Will
calculate Ms, Hc, and squareness.""")
    p.add_argument('-r','--hard', action='store_true',
        help="""Indicate that loop(s) are hard-axis loops. Will
calculate Ms, Hk, and Mr.""")
    p.add_argument('-n', '--negate', action='store_true',
        help="""Add a 180 degree phase shift (i.e. negate) moment data
prior to calculation.""")
    p.add_argument('-p', '--plot', action='store_true',
        help="""create a plot of the hysyeresis loop with the
calculated points marked on it.""")
    p.add_argument('--hk-radius', metavar='R', default=4.0,
    type=float, help="""Range of data points to calculate Hk.
Calculation will be done with data points H=[-R,R].""")
    return p


def getdata(fp):
    a=pd.read_csv(fp, header=9,sep='\t', names=['h','m'])
    return np.array(a['h']), np.array(a['m'])


def getms(hup, mup, hdn, mdn):
    return ms1d(mup)
    
    
def ms1d(m):
    mflat = []
    m0 = m[0]
    for mk in m:
        if abs((mk-m0)/m0) < 0.1:
            mflat.append(mk)
    return abs(np.mean(mflat))


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
    return hplt, mplt, hk


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


def splitupdn(hpts, mpts):
    hup = []
    mup = []
    hdn = []
    mdn = []
    dh = np.diff(hpts)
    for k,dhk in enumerate(dh):
        if dhk > 0:
            hup.append(hpts[k])
            mup.append(mpts[k])
        else:
            hdn.append(hpts[k])
            mdn.append(mpts[k])
    return hup, mup, hdn, mdn


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


if __name__ == '__main__':
    main()
