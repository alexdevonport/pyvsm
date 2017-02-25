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

def main():
    parser = mkparser()
    args = parser.parse_args()
    if args.credits:
        print(credits)
        sys.exit()
    easyax = getaxis(args)
    if easyax:
        names = ['file', 'ms', 'hc', 'mr', 'sqr']
    else:
        names = ['file', 'ms', 'hk']
    print(args.delimiter.join(names))
    for fp in args.files:
        h, m = getdata(fp)
        if args.negate:
            m *= -1
        hup, mup, hdn, mdn = splitupdn(h,m)
        hup, hdn = centerh(hup, mup, hdn, mdn)
        mupfit, mdnfit, results = analyze_data(hup, mup, hdn, mdn, 
            fp, easyax)
        dataname = os.path.basename(fp)
        print(dataname, end=args.delimiter)
        for r in results:
            print('{:.4g}'.format(r),end=args.delimiter)
        print()
        if args.plot:
            plot_results(hup, mup, hdn, mdn, 
                mupfit, mdnfit, dataname, args.save)
    plt.close()
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

def analyze_data(hup, mup, hdn, mdn, fp, easyax):
    #ms, hsw, hk, moffs
    rh = 1.0  # range around swiching point (in Oe) to estimate Hk with
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
    if easyax:
        return bfup, bfdn, [ms, hc, mr, sqr]
    else:
        return bfup, bfdn, [ms, hk]


def plot_results(hup, mup, hdn, mdn, mupfit, mdnfit, dataname, saving):
    fig, ax = plt.subplots(figsize=(5,4),dpi=100)
    fig.patch.set_facecolor('white')
    ax.plot(hup, np.array(mup)*1E6, color='k', 
        ls='None', marker='.', ms=5)
    ax.plot(hdn, np.array(mdn)*1E6, color='k', 
        ls='None', marker='.', ms=5, label='data')
    ax.plot(hup, np.array(mupfit)*1E6, color='b')
    ax.plot(hdn, np.array(mdnfit)*1E6, color='b', label='fit')
    ax.set_xlabel('field (Oe)')
    ax.set_ylabel('moment ($\mathsf{\mu}$emu)')
    ax.legend(loc='best')
    ax.set_title('M-H loop of {:s}'.format(dataname))
    fig.tight_layout()
    if saving:
        plt.savefig('MHLOOP-{:s}.png'.format(dataname), dpi=300)
    else:
        plt.show()
    return None



def analyze_hard(hup, mup, hdn, mdn, fp, rh, mkplt=True):
    hplt, mplt, hk= gethk(hup, mup, hdn, mdn, rh)
    ms = getms(hup, mup, hdn, mdn)
    hc = gethc(hup, mup, hdn, mdn)
    dataname = os.path.splitext(os.path.basename(fp))[0]
    #print('file={:s} ms={:.4g} hk={:.4g}'.format(dataname, ms, hk))
    if mkplt:
        plot_hard(hup, mup, hdn, mdn, hplt, mplt, ms, hk, fp, dataname)
    return [ms, hk]


def plot_hard(hup, mup, hdn, mdn, hplt, mplt, ms, hk, fp, name):
    plt.plot(hup, mup, 'g', label='M-H loop data')
    plt.plot(hdn, mdn, 'g')
    plt.plot(hplt, mplt, 'b', label='hk extrapolation')
    hms1 = np.linspace(hup[0], -hk, 100)
    hms2 = np.linspace(hk, hup[-1],100)
    ms0 = math.copysign(ms,mup[0])
    ms1 = math.copysign(ms,mup[-1])
    plt.plot([hup[0], -hk],[ms0, ms0], 'b')
    plt.plot([hk,hup[-1]],[ms1,ms1], 'b')
    plt.title('hard axis MH loop for {:s}'.format(name))
    plt.legend(loc='best')
    plt.grid(True)
    plt.show()
    return None


def analyze_easy(hup, mup, hdn, mdn, fp, mkplt=True):
    ms = getms(hup, mup, hdn, mdn)
    hc = gethc(hup, mup, hdn, mdn)
    mr = getmr(hup, mup, hdn, mdn)
    sqr = mr / ms
    dataname = os.path.splitext(os.path.basename(fp))[0]
    #print("""file={:s} ms={:.4g} hc={:.4g}\
# mr={:.4g} sqr={:.4g}""".format(dataname, ms, hc, mr, sqr))
    if mkplt:
        plot_easy(hup, mup, hdn, mdn, fp, ms, hc, mr, dataname)
    return [ms, hc, mr, sqr]


def plot_easy(hup, mup, hdn, mdn, fp, ms, hc, mr, name):
    plt.plot(hup, mup, 'k', label='M-H loop data')
    plt.plot(hdn, mdn, 'k')
    plt.plot([-hc, -hc],[-ms, ms], 'b--', label='ideal (sqr=1) loop') 
    plt.plot([hc, hc], [-ms, ms], 'b--')
    plt.plot([-hc, hc], [ms, ms], 'b--')
    plt.plot([-hc, hc], [-ms, -ms], 'b--')
    plt.plot([0, 0], [mr, mr], 'ro ', label='mr')
    plt.title('Easy axis MH loop for {:s}'.format(name))
    plt.legend(loc='best')
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
"""
    p = argparse.ArgumentParser(description=desc, epilog=epi,
        formatter_class=argparse.RawDescriptionHelpFormatter,)
    p.add_argument('files', type=str, metavar='FILE', nargs='*',
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
    p.add_argument('-s', '--save', action='store_true',
        help="""Save an image of the MH loop data and fit.""")
    p.add_argument('--hk-radius', metavar='R', default=4.0,
        type=float, help="""Range of data points to calculate Hk.
        Calculation will be done with data points H=[-R,R].""")
    p.add_argument('-d', '--delimiter', action='store',
        default=' ', type=str, metavar='D', help="""
        Character (or characters) used to separate analysis
        values on a single line.
        """)
    p.add_argument('--credits', action='store_true',
        help="""display credits and exit.""")
    return p


def getdata(fp):
    a=pd.read_csv(fp, header=9,sep='\t', names=['h','m'])
    return np.array(a['h']), np.array(a['m'])


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

if __name__ == '__main__':
    main()
