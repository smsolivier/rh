#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

import Timer 

import os 
import sys 

import shutil 

class Transport:
	''' general transport initialization ''' 

	def __init__(self, xe, n, Sigmaa, Sigmat, q, BCL=0, BCR=1):
		''' Inputs:
				xe: cell edges 
				n: number of discrete ordinates 
				Sigmaa: absorption XS (function)
				Sigmat: total XS (function)
				q: fixed source array of mu and cell center spatial dependence 
		''' 

		self.name = None # store name of methods

		self.N = np.shape(xe)[0] - 1 # number of cell centers 
		self.Ne = np.shape(xe)[0] # number of cell edges 
		self.n = n # number of discrete ordinates 
		
		# left and right boundary conditions 
		self.BCL = BCL
		self.BCR = BCR 

		self.h = np.zeros(self.N) # cell widths at cell center 
		self.xc = np.zeros(self.N) # cell centered locations 
		self.xe = xe # cell edge array 

		# use cell edge in source iteration, self.x is returned in source iteration  
		self.x = self.xe 

		self.xb = xe[-1] # end of domain 

		# get cell centers and cell widths 
		for i in range(1, self.Ne):

			self.xc[i-1] = .5*(xe[i] + xe[i-1]) # get cell centers 
			self.h[i-1] = xe[i] - xe[i-1] # get cell widths 

		assert(n%2 == 0) # assert number of discrete ordinates is even 

		# make material properties public 
		self.Sigmaa = Sigmaa 
		self.Sigmat = Sigmat 
		self.Sigmas = lambda x: Sigmat(x) - Sigmaa(x)
		self.q = q 

		# ensure q is correct shape 
		if (np.shape(self.q)[0] != self.n):

			print('\n--- FATAL ERROR: Transport q must have correct angular dependence ---\n')
			sys.exit()

		if (np.shape(self.q)[1] != self.N):

			print('\n--- FATAL ERROR: Transport q must be cell centered ---')
			sys.exit()

		# initialize psi and phi 
		self.psi = np.zeros((self.n, self.Ne)) # cell edged flux 
		self.phi = np.zeros(self.Ne) # store flux 

		# generate mu's, mu is arranged negative to positive 
		self.mu, self.w = np.polynomial.legendre.leggauss(n)

	def setMMS(self):
		''' setup MMS q 
			force phi = sin(pi*x/xb)
		''' 

		# ensure correct BCs 
		self.BCL = 1 
		self.BCR = 1 

		# loop through all angles 
		for i in range(self.n):

			# loop through space 
			for j in range(self.N):

				self.q[i,j] = self.mu[i]*np.pi/self.xb * \
					np.cos(np.pi*self.xc[j]/self.xb) + (self.Sigmat(self.xc[j]) - 
						self.Sigmas(self.xc[j]))*np.sin(np.pi*self.xc[j]/self.xb)

	def zeroMoment(self, psi):
		''' use guass legendre quadrature points to integrate psi ''' 

		phi = np.zeros(np.shape(psi)[1])

		for i in range(self.n):

			phi += psi[i,:] * self.w[i] 

		return phi 

	def firstMoment(self, psi):
		''' use guass quadrature to integrate mu psi ''' 

		J = np.zeros(np.shape(psi)[1])

		for i in range(self.n):

			J += self.mu[i] * psi[i,:] * self.w[i] 

		return J 

	def getEddington(self, psi):
		''' compute <mu^2> ''' 

		phi = self.zeroMoment(psi)

		# Eddington factor 
		mu2 = np.zeros(np.shape(psi)[1]) 

		top = 0 
		for i in range(self.n):

			top += self.mu[i]**2 * psi[i,:] * self.w[i] 

		mu2 = top/phi 

		return mu2

	def sourceIteration(self, tol, maxIter=50, PLOT=None):
		''' lag RHS of transport equation and iterate until flux converges ''' 

		it = 0 # store number of iterations 

		tt = Timer.timer()

		self.phiConv = [] # store convergence criterion for flux 

		if (PLOT != None):

			if (os.path.isdir(PLOT)):

				shutil.rmtree(PLOT)

			os.makedirs(PLOT)

			if (os.path.isfile(PLOT + '.mp4')):

				os.remove(PLOT + '.mp4')

		while (True):

			# check if max reached 
			if (it == maxIter):

				print('\n--- WARNING: maximum number of source iterations reached ---\n')
				break 

			# store old flux 
			phi_old = np.copy(self.phi) 

			if (PLOT != None):
				
				plt.figure()
				plt.plot(self.x, self.phi, '-o')
				# plt.ylim(0, 1.2)
				plt.title('Number of Iterations = ' + str(it))
				plt.savefig(PLOT + '/' + str(it) + '.png')
				plt.close()

			self.phi = self.sweep(phi_old) # update flux 

			self.phiConv.append(np.linalg.norm(self.phi - phi_old, 2)/
				np.linalg.norm(self.phi, 2))

			# check for convergence 
			if (self.phiConv[-1] < tol):

				break 

			# update iteration count 
			it += 1

			print(it, end='\r')

		print('Number of iterations =', it, end=', ') 
		tt.stop()

		if (PLOT != None):

			# make video 
			os.system('ffmpeg -f image2 -r 2 -i ' + PLOT + '/%d.png -b 320000k ' + PLOT + '.mp4')

		# return spatial locations, flux and number of iterations 
		return self.x, self.phi, it 

