#TODO : remove camelCase

import random, string
from collections import namedtuple 
from petlib.ec import EcGroup
from petlib.bn import Bn
from SigmaProtocol import *


class PedersenProver(Prover):
	def commit(self):
		tab_g= self.params.tab_g
		public_info = self.params.public_info
		
		o = tab_g[0].group.order()
		self.ks = []
		for i in range(len(tab_g)): #we build a N-commitments
			self.ks.append(o.random())
		# one could create an array ks and secrets to generalize this algorithm. 
		# with |array of ks| = 1 and |array of secrets| = 1 we would obtain the schnorr zkp
		commitment = [a*b for a,b in zip(self.ks, tab_g)]
		
		print ('\ncommitment = ', commitment, '\npublic_info = ', public_info)
		return commitment #Do we return public info here or is it already accessible to the Verifier?

	def computeResponse(self, challenge): #r = secret*challenge + k 
		resps = [(self.params.secrets[i].mod_mul(challenge,o)).mod_add(self.ks[i],o) for i in range(len(self.ks))]
		print('\n responses : ', resps)
		return resps

	def sendResponse(self, challenge):
		response = self.computeResponse(challenge) #could create a private non defined method called compute response in an interface Prover
		return response

class PedersenVerifier(Verifier):

	def sendChallenge(self, commitment):
		tab_g = self.params.tab_g
		self.o = tab_g[0].group.order()
		self.commitment = commitment
		self.challenge = self.o.random()
		print('\nchallenge is ', self.challenge)
		return self.challenge
					
	def verify(self, response):
		tab_g = self.params.tab_g
		y = self.params.public_info 
		r = self.commitment
		G = tab_g[0].group

		
		leftSide =  [a*b for a,b in zip(response, tab_g)]
		
		sumleft = G.infinite()
		#sumleft = leftSide[0] #Ugly but simpler than converting 0 in Bn
		for i in range(len(leftSide)):
			sumleft+= leftSide[i]
		#leftSide = (response[0] * g1) + (response[1] * g2) ...

		#rightSide = (challenge * y1 + r1) + (challenge*y2+r2) ...
		# (generalization of rightSide = challenge*y + r in Schnorr)
		rightSide = [self.challenge*yelem + relem for yelem, relem in zip(y, r)]
		sumright = G.infinite()
	    #sumright = rightSide[0] #Ugly but simpler than converting 0 in Bn
		for i in range(len(rightSide)):
			sumright+= rightSide[i]

		if sumright == sumleft: #If the result
			print("Verified")
		else:
			print("Not verified")

def randomword(length):
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(length))

class PedersenProtocol(SigmaProtocol):
	def __init__(self, verifierClass, proverClass, public_info, tab_g, secrets):
		super().__init__(verifierClass, proverClass)
		if len(tab_g) != len(secrets):
			raise Exception('One secret = one generator, one voice one hope one real decision...')
		self.params = Params(public_info, tab_g, secrets)

		test_group = tab_g[0].group
		for g in tab_g:
			if g.group != test_group:
				raise Exception('All generators should come from the same group')

	def setup(self): #for compatibility with the SigmaProtocol class
			params_verif = Params(public_info, tab_g, None) #we build a custom parameter object without the secrets 
			return self.params, params_verif

N = 5
G = EcGroup(713)
tab_g = []
tab_g.append(G.generator())
for i in range (1,N):
	randWord = randomword(30).encode("UTF-8")
	tab_g.append(G.hash_to_point(randWord)) 
o = G.order()
secrets = []
for i in range(len(tab_g)): #we build N secrets
	secrets.append(o.random())# peggy wishes to prove she knows the discrete logarithm equal to this value

public_info = [a*b for a,b in zip (secrets, tab_g)] #The Ys of which we will prove logarithm knowledge

pedersenProtocol = PedersenProtocol(PedersenVerifier, PedersenProver, public_info, tab_g, secrets)
pedersenProtocol.run()