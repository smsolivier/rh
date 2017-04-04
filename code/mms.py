#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

import ld as LD
import dd as DD 

from scipy.interpolate import interp1d 

from hidespines import * 

from R2 import * 

import sys 

''' Test MMS functions in LD and DD ''' 

if (len(sys.argv) > 1):
	outfile = sys.argv[1] 
else:
	outfile = None 

def getOrder(sol, N, tol, label):

	print('Method =', sol[0].name)

	phi_mms = lambda x: np.sin(np.pi*x/xb) # exact solution 

	err = np.zeros(len(sol))
	for i in range(len(sol)):

		sol[i].setMMS()
		# make video 
		# x, phi, it = sol[i].sourceIteration(tol, PLOT='phi' + str(N[i]))
		x, phi, it = sol[i].sourceIteration(tol, 1000)

		phi_int = interp1d(x, phi)

		# err[i] = np.fabs(phi_mms(xb/2) - phi_int(xb/2))/phi_mms(xb/2)
		err[i] = np.linalg.norm(phi_mms(x) - phi, 2)/np.linalg.norm(phi_mms(x), 2)

	# 	plt.plot(x, phi, '-o')

	# plt.show()

	fit = np.polyfit(np.log(1/N), np.log(err), 1)

	# fit equation 
	f = lambda x: np.exp(fit[1]) * x**(fit[0])

	# R^2 value
	r2 = rsquared(err, f(1/N))

	print(fit[0], fit[1], r2)

	plt.loglog(xb/N, err, '-o', clip_on=False, label=label)

	return err

N = np.array([80, 160, 320, 640])

n = 8 

Sigmaa = lambda x: .1
Sigmat = lambda x: 1

xb = 5

tol = 1e-10 

# make solver objects 
ed00 = [LD.Eddington(np.linspace(0, xb, x+1), n, Sigmaa, 
	Sigmat, np.ones((n, x)), OPT=0, GAUSS=0) for x in N]

ed01 = [LD.Eddington(np.linspace(0, xb, x+1), n, Sigmaa, 
	Sigmat, np.ones((n, x)), OPT=0, GAUSS=1) for x in N]

ed10 = [LD.Eddington(np.linspace(0, xb, x+1), n, Sigmaa, 
	Sigmat, np.ones((n, x)), OPT=1, GAUSS=0) for x in N]

ed11 = [LD.Eddington(np.linspace(0, xb, x+1), n, Sigmaa, 
	Sigmat, np.ones((n, x)), OPT=1, GAUSS=1) for x in N]

ed20 = [LD.Eddington(np.linspace(0, xb, x+1), n, Sigmaa, 
	Sigmat, np.ones((n,x)), OPT=2, GAUSS=0) for x in N]

ed21 = [LD.Eddington(np.linspace(0, xb, x+1), n, Sigmaa, 
	Sigmat, np.ones((n, x)), OPT=2, GAUSS=1) for x in N]

# get order of accuracy 
err00 = getOrder(ed00, N, tol, 'MHFEM Edges, No Gauss')
err01 = getOrder(ed01, N, tol, 'Maintain Slopes, No Gauss')
err10 = getOrder(ed10, N, tol, 'MHFEM Edges, Gauss')
err11 = getOrder(ed11, N, tol, 'Maintain Slopes, Gauss')
err20 = getOrder(ed20, N, tol, 'vanLeer, No Gauss')
err21 = getOrder(ed21, N, tol, 'vanLeer, Gauss')

plt.loglog(xb/N, err20[-1]/(xb/N[-1])**2*(xb/N)**2, 
	color='k', alpha=.7, label='Slope = 2')
plt.legend(loc='best', frameon=False)
plt.xlabel(r'$h$', fontsize=20)
plt.ylabel('Error', fontsize=20)
hidespines(plt.gca())
if (outfile != None):
	plt.savefig(outfile, transparent=True)
else:
	plt.show()