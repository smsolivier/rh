#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

import sn as DD

class LD:

	def __init__(self, xe, n, Sigmaa, Sigmat, q):
		''' 
			Inputs:
				xe: cell edges 
				n: number of discrete ordinates 
				Sigmaa: absorption XS (function)
				Sigmat: total XS (function)
				q: fixed source (cell edged array)
		''' 

		self.N = np.shape(xe)[0] - 1 # number of cell centers 
		self.n = n # number of discrete ordinates 

		self.x = np.zeros(self.N) # cell centered locations 
		self.h = np.zeros(self.N) # cell widths at cell center 

		for i in range(1, self.N+1):

			self.x[i-1] = .5*(xe[i] + xe[i-1])
			self.h[i-1] = xe[i] - xe[i-1] 

		assert(n%2 == 0) # assert n is even 

		# make material properties public 
		self.Sigmaa = Sigmaa 
		self.Sigmat = Sigmat 
		self.Sigmas = lambda x: Sigmat(x) - Sigmaa(x)
		self.q = q 

		# store LD left and right discontinuous points 
		# psi = .5*(psiL + psiR) 
		# store for all mu and each cell center 
		self.psiL = np.zeros((self.n, self.N)) # LD left point  
		self.psiR = np.zeros((self.n, self.N)) # LD right point 

		self.phi = np.zeros(self.N) # store flux 

		# generate mu's, mu is arranged negative to positive 
		self.mu, self.w = np.polynomial.legendre.leggauss(n)

	def sweep(self, phiL, phiR):

		self.sweepRL(phiL, phiR)
		self.sweepLR(phiL, phiR)

		phiL, phiR = self.integratePsi()

		return phiL, phiR 

	def sweepLR(self, phiL, phiR):
		''' sweep left to right (mu > 0) ''' 

		A = np.zeros((2,2)) # store psiL, psiR coefficients 
		b = np.zeros(2) # store rhs 

		# loop through positive angles 
		for i in range(int(self.n/2), self.n):

			# loop from 1:N, assume BC already set 
			for j in range(0, self.N):

				h = self.h[j] # cell width 

				# left equation 
				A[0,0] = self.mu[i]/2 + self.Sigmat(self.x[j])*h/2 # psiL 
				A[0,1] = self.mu[i]/2 # psiR 

				# right equation 
				A[1,0] = -self.mu[i]/2 # psiL
				A[1,1] = -self.mu[i]/2 + self.Sigmat(self.x[j])*h/2 + self.mu[i] # psiR 

				# rhs 
				b[0] = self.Sigmas(self.x[j])*h/4*phiL[j] + self.q[i]*h/4 # left 
				if (j == 0):
					b[0] += self.mu[i]*self.psiL[self.mu == -self.mu[i],0]
				else:
					b[0] += self.mu[i]*self.psiR[i,j-1] # upwind term 
				b[1] = self.Sigmas(self.x[j])*h/4*phiR[j] + self.q[i+1]*h/4 # right 

				ans = np.linalg.solve(A, b) # solve for psiL, psiR 

				# extract psis 
				self.psiL[i,j] = ans[0] 
				self.psiR[i,j] = ans[1] 

	def sweepRL(self, phiL, phiR):
		''' sweep right to left (mu < 0) ''' 

		A = np.zeros((2,2)) # store psiL, psiR coefficients 
		b = np.zeros(2) # store rhs 

		# loop through negative angles 
		for i in range(int(self.n/2)):

			# loop backwards from N-1:0, assume BC already set 
			for j in range(self.N-1, -1, -1):

				h = self.h[j] # cell width 

				# left equation 
				A[1,0] = -self.mu[i]/2 # psiL
				A[1,1] = -self.mu[i]/2 + self.Sigmat(self.x[j])*h/2 # psiR 

				# right equation 
				A[0,0] = self.mu[i]/2 + self.Sigmat(self.x[j])*h/2 - self.mu[i] # psiL 
				A[0,1] = self.mu[i]/2 

				# rhs 
				b[0] = self.Sigmas(self.x[j])*h/4*phiL[j] + self.q[i]*h/4 # left 
				b[1] = self.Sigmas(self.x[j])*h/4*phiR[j] + self.q[i+1]*h/4 # right 
				if (j != self.N-1):
					b[1] -= self.mu[i]*self.psiL[i,j+1] # downwind term 

				ans = np.linalg.solve(A, b) # solve for psiL, psiR 

				# extract psis 
				self.psiL[i,j] = ans[0] 
				self.psiR[i,j] = ans[1] 

	def integratePsi(self):
		''' use guass legendre quadrature points to integrate psi ''' 

		phi = np.zeros(self.N)

		phiL = np.zeros(self.N) # store LD left flux 
		phiR = np.zeros(self.N) # store LD right flux 

		# loop through angles
		for i in range(self.n):

			phiL += self.psiL[i,:] * self.w[i] 
			phiR += self.psiR[i,:] * self.w[i]

		return phiL, phiR 

	def getEddington(self):
		''' compute Eddington factor ''' 

		# compute <mu^2> 
		top = 0 # store int mu^2 psi dmu 
		# loop through angles
		for i in range(int(self.n/2)):

			top += self.muR[i]**2*self.psiL[i,:] * self.wL[i] + \
				self.muR[i]**2*self.psiR[i,:] * self.wR[i]

		mu2 = top/self.integratePsi()

		return mu2 

	def edgeFlux(self):

		psi = np.zeros((self.n, self.N+1)) # store cell edge flux 

		for i in range(self.n):

			if (self.mu[i] > 0):

				# set boundary values 
				psi[i,0] = self.psiL[self.mu == -self.mu[i],0]

				for j in range(self.N):

					psi[i,j+1] = self.psiR[i,j] 

			else:

				# set boundary values 
				psi[i,-1] = 0 

				for j in range(self.N-1, -1, -1):

					psi[i,j] = self.psiL[i,j]

		phi = np.zeros(self.N + 1) # cell edge flux 

		for i in range(self.n):

			phi += psi[i,:] * self.w[i]

		return phi 



	def sourceIteration(self, tol, PLOT=False):
		''' lag RHS of transport equation and iterate until flux converges ''' 

		it = 0 # store number of iterations 
		phiL = np.zeros(self.N) # LD left flux 
		phiR = np.zeros(self.N) # LD right flux 
		phi = np.zeros(self.N) # cell centered flux 
		edd = np.zeros(self.N) # store eddington factor 

		self.phiCon = [] 
		self.eddCon = [] 

		while (True):

			# store old flux 
			phi_old = np.copy(phi) 

			phiL, phiR = self.sweep(phiL, phiR) # update flux 

			phi = .5*(phiL + phiR) # cell centered flux 

			self.phiCon.append(np.linalg.norm(phi - phi_old, 2)/np.linalg.norm(phi, 2))

			# check for convergence 
			if (np.linalg.norm(phi - phi_old, 2)/np.linalg.norm(phi, 2) < tol):

				break 

			# update iteration count 
			it += 1 

		print('Number of iterations =', it) 

		if (PLOT):
			for i in range(int(self.n/2)):
				plt.plot(self.x, self.psiL[i,:], label=str(self.muL[i]))
				plt.plot(self.x, self.psiR[i,:], label=str(self.muR[i]))

			plt.legend(loc='best')
			plt.show()

		# return spatial locations, flux and number of iterations 
		return self.x, phi, it 
N = 20
xb = 2
x = np.linspace(0, xb, N)
Sigmaa = lambda x: .1 
Sigmat = lambda x: .83 
q = np.ones(N) 

n = 8

ld = LD(x, n, Sigmaa, Sigmat, q)

sn = DD.Sn(x, n, Sigmaa, Sigmat, q)

xc, phi, it = ld.sourceIteration(1e-6)
phi = ld.edgeFlux()

xsn, phisn, itsn = sn.sourceIteration(1e-6)

plt.plot(x, phi, label='LD')
plt.plot(xsn, phisn, label='DD')
plt.legend(loc='best')
plt.show()