# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 11:37:00 2021

@author: rimmler
"""

# ____________________________________________________________________________
# SETTINGS
import numpy as np

g = 2.07
t = 16.5 # SH material film thickness in nm
terr = .5
d = 3. # FM thickness in nm
derr = .3
Ms = 900 # saturation magnetization FM layer emu/cm3
Mserr = 20

plotDpi = 600



# ____________________________________________________________________________
# Constants
mu0 = 4*np.pi*1e-7
e = 1.60218e-19 # C
me = 9.10938e-31 # kg
hbar = 1.054578e-34 # J s
gamma = e * g / (2 * me)

# ____________________________________________________________________________
# CODE
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


class File:
    def __init__(self, file):
        self.file_fulldir = file
        self.filedir = '/'.join(file.split('/')[:-1])
        self.filename = file.split('/')[-1]
        self.fileext = '.' + self.filename.split('.')[-1]
        self.filename_wo_ext = '.'.join(self.filename.split('.')[:-1])

def kittel(H0, Meff, gamma, mu0):
    ''' With same unit system! '''
    f = gamma * mu0 / (2*np.pi) * np.sqrt(H0 * (H0 + Meff))

    return f

def gilbert(f, mu0, gamma, alpha, delta0):
    ''' Everything in SI '''
    # print('GILBERT')
    delta = f * 2*np.pi*alpha / (mu0 * gamma) + delta0

    # print(f)
    # print(gamma, alpha, delta0)
    # print(delta)
    return delta

def get_SHA(Vs, Va, Ms, t, d, hbar, Meff, H0):
    return Vs/Va * (2*e*mu0*Ms*t*d) / (2*hbar) * np.sqrt(1 + Meff/H0)

def get_SHAerr(e, mu0, hbar, Vs, Va, Ms, t, d, Meff, H0,
               d_Vs, d_Va, d_Ms, d_t, d_d, d_Meff, d_H0):
    c = e * mu0 / hbar
    sq = np.sqrt(1+Meff/H0)
    T1 = ( Ms*t*d/Va*sq*d_Vs )**2
    T2 = ( Vs/Va**2 *Ms*t*d*sq*d_Va)**2
    T3 = ( Vs/Va*t*d*sq*d_Ms )**2
    T4 = ( Vs/Va *Ms*d*sq*d_t)**2
    T5 = ( Vs/Va*Ms*t*sq*d_d)**2
    T6 = ( Vs/Va*Ms*t*d/2*(1+Meff/H0)**(-1/2)/H0*d_Meff )**2
    T7 = ( Vs/Va*Ms*t*d/2*(1*Meff/H0)**(-1/2)*Meff/H0**2*d_H0 )**2

    return c * np.sqrt(T1+T2+T3+T4+T5+T6+T7)

def cgssi(quantity, value, conv):
    if quantity == 'H':
        c = 1e3/(4*np.pi)
    elif quantity == 'B':
        c = 1e-4
    elif quantity == 'M':
        c = 1e3
    elif quantity == 'gamma':
        c = 4*np.pi*1e-3
    elif quantity == 'mu0':
        c = 4*np.pi*1e-7
    else:
        raise ValueError('Quantity not defined')
    if conv == 'fw': # forward
        return value * c
    elif conv == 'bw': # backward
        return value / c
    else:
        raise ValueError('Sense of conversion not defined')

def fit_kittel(H0SI, f, I, P, gamma, mu0):
    fopt, fcov = curve_fit(lambda x, a: kittel(x, a, gamma, mu0), H0SI, f*1e9)
    Meffopt = fopt[0]
    Meffopterr = np.sqrt(np.diag(fcov))[0]
    MeffoptCGS = cgssi('M', Meffopt, 'bw')
    MeffopterrCGS = cgssi('M', Meffopterr, 'bw')
    ffit = kittel(H0SI, Meffopt, gamma, mu0)

    fig = plt.figure()
    # plt.errorbar(H0, f, xerr=H0err, fmt='o')
    plt.plot(H0, f, ':o', label='Data')
    plt.plot(H0, ffit*1e-9, '', label='Fit')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.xlabel('$H_0$ (Oe)')
    plt.ylabel('f (GHz)')
    plt.legend(loc='lower right')
    plt.title('Fit to Kittel formula')
    boxtext = '\n'.join((
        'I = {} mA \nP = {} dBm'.format(I, P),
        r'$M_{eff}^{fit}=$'+'$({:.0f} \pm {:.0f})$ '.format(MeffoptCGS, MeffopterrCGS)+'emu/cm$^3$'))
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    ax = plt.gca()
    ax.text(0.03, 0.97, boxtext, verticalalignment='top',
            transform=ax.transAxes, bbox=props, fontsize=10)

    plt.show()
    fig.savefig(outputFileKittel.file_fulldir, bbox_inches="tight", dpi=plotDpi)

    return MeffoptCGS, MeffopterrCGS

def fit_gilbert(f, DeltaSI, gamma):
    ''' f in GHz, rest in SI '''
    popt, pcov = curve_fit(lambda x, a, b: gilbert(x, mu0, gamma, a, b), f*1e9, DeltaSI)

    alphaopt = popt[0]
    alphaopterr = np.sqrt(np.diag(pcov))[0]

    delta0opt = popt[1]
    delta0opterr = np.sqrt(np.diag(pcov))[1]
    delta0optCGS = cgssi('H', delta0opt, 'bw')
    delta0opterrCGS = cgssi('H', delta0opterr, 'bw')

    Deltafit = gilbert(f*1e9, mu0, gamma, alphaopt, delta0opt)

    fig = plt.figure(dpi=600)
    plt.plot(f, cgssi('H', DeltaSI, 'bw'), ':o', label='Data')
    plt.plot(f, cgssi('H', Deltafit, 'bw'), label='Fit')
    # plt.plot(f, DeltaSI, ':o', label='Data')
    # plt.plot(f, Deltafit, label='Fit')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.xlabel('$f$ (GHz)')
    plt.ylabel('$\Delta$ (Oe)')
    plt.legend(loc='lower right')
    plt.title('Gilbert fitting')

    boxtext = '\n'.join((
        'I = {} mA \nP = {} dBm'.format(I, P),
        r'$\alpha^{fit}=$'+'$({:.4f} \pm {:.4f})$ '.format(alphaopt, alphaopterr),
        r'$\Delta_{0}^{fit}=$'+'$({:.1f} \pm {:.1f})$ '.format(delta0optCGS, delta0opterrCGS)+'Oe'))
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    ax = plt.gca()
    ax.text(0.03, 0.97, boxtext, verticalalignment='top',
            transform=ax.transAxes, bbox=props, fontsize=10)

    plt.show()
    fig.savefig(outputFileGilbert.file_fulldir, bbox_inches="tight", dpi=plotDpi)

    return alphaopt, alphaopterr, popt, pcov

def lineshapeAnalysis(Vs, Va, MsSI, t, d, hbar, MeffoptSI, H0SI, Vserr, Vaerr, Mserr, derr, terr, MeffopterrSI, H0errSI):
    SHA = get_SHA(Vs, Va, MsSI, t, d, hbar, MeffoptSI, H0SI)
    SHAerr = get_SHAerr(e, mu0, hbar, Vs, Va, MsSI, t, d, MeffoptSI, H0SI, Vserr, Vaerr, Mserr, derr, terr, MeffopterrSI, H0errSI)

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    # ax1.scatter(H0, Vs*1e6, label='Vs')
    ax1.plot(H0, Vs*1e6, ':o', label='Vs')
    ax1.plot(H0, Va*1e6, ':o', label='Va')
    ax2.errorbar(H0, SHA, yerr=SHAerr, ls=':', marker='o', c='g', capsize=2, label='SHA')

    plt.xlim(left=0)
    # plt.ylim(bottom=0)
    ax1.set_xlabel('$H_0$ (Oe)')
    ax1.set_ylabel('$V_{i}$ ($\mu$V)')
    ax2.set_ylabel('$\Theta_{sh}$')

    fig.legend(bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)

    plt.title('Line shape analysis')
    plt.show()
    fig.savefig(outputFileLS1.file_fulldir, bbox_inches="tight", dpi=plotDpi)
    return SHA, SHAerr


# ____________________________________________________________________________
root = tk.Tk()
root.withdraw()
# inputFile = File(filedialog.askopenfilename(parent=root, title='Choose .csv file with fitting summary'))
inputFile = File('D:/ANALYSIS/Mn3SnN/ST-FMR/MA2427-1/210401/003_lineshape_15dBm/fittingOutput/000_fittingSummary.csv')
outputFileGilbert = File(inputFile.filedir + '/' + inputFile.filename_wo_ext + '_gilbertFit.png')
outputFileKittel = File(inputFile.filedir + '/' + inputFile.filename_wo_ext + '_kittelFit.png')
outputFileLS1 = File(inputFile.filedir + '/' + inputFile.filename_wo_ext + '_shaPlot.png')

inputData = pd.read_csv(inputFile.file_fulldir,index_col=False)

# Fit Kittel formula to get Meff
f = inputData['Frequency (GHz)']#.sort_values()
H0 = inputData['Hres (Oe)']#.sort_values()
H0SI = cgssi('H', H0, 'fw')
H0err = inputData['HresError (Oe)']
H0errSI = cgssi('H', H0err, 'fw')

I = float(inputData['Current (mA)'][0])
P = float(inputData['rf Power (dBm)'][0])

MeffoptCGS, MeffopterrCGS = fit_kittel(H0SI, f, I, P, gamma, mu0)
MeffoptSI = cgssi('M', MeffoptCGS, 'fw')
MeffopterrSI = cgssi('M', MeffopterrCGS, 'fw')

# Fit Gilbert equation to get Gilbert damping
Delta = inputData['DeltaH (Oe)']

alphaopt, alphaopterr, popt, pcov = fit_gilbert(f, cgssi('H', Delta, 'fw'), gamma)

# Calculate SHA and plot against H0
t *= 1e-9
terr *= 1e-9
d *= 1e-9
derr *= 1e-9
MsSI = cgssi('M', Ms, 'fw')
MserrSI = cgssi('M', Mserr, 'fw')

Vs = inputData['Vsym (V)']
Va = inputData['Vas (V)']
Vserr = inputData['VsymError (V)']
Vaerr = inputData['VasError (V)']

lsSHA, lsSHAerr = lineshapeAnalysis(Vs, Va, MsSI, t, d, hbar, MeffoptSI, H0SI, Vserr, Vaerr, Mserr, derr, terr, MeffopterrSI, H0errSI)

outputData1 = inputData
outputData1['HresSI (A/m)'] = H0
outputData1['HresError SI (A/m)'] = H0errSI
outputData1['SHA'] = lsSHA
outputData1['SHAError'] = lsSHAerr

summary = {'g': g,
           't (nm)': t,
           'tError (nm)': terr,
           'd (nm)': d,
           'dError (nm)': derr,
           'Ms (emu/cm3)': Ms,
           'MsError (emu/cm3)': Mserr,
           'Meffopt (emu/cm3)': MeffoptCGS,
           'MeffoptError (emu/cm3)': MeffopterrCGS
           }

outputData2 = pd.Series(summary)

outputFileLS2 = File(inputFile.filedir + '/' + inputFile.filename_wo_ext + '_lsOuput1.csv')
outputFileLS3 = File(inputFile.filedir + '/' + inputFile.filename_wo_ext + '_lsOuput2.csv')

outputData1.to_csv(outputFileLS2.file_fulldir, index=False)
outputData2.to_csv(outputFileLS3.file_fulldir, header=False)











