# Import packages
import numpy as np # For efficient array operations
import matplotlib as mpl
import matplotlib.pyplot as plt # For plotting
import time # For timing parts of the script, optimizing run time
import profile
import pandas as pd
#import multiprocessing
#from multiprocessing.pool import ThreadPool

try:
	import seaborn as sns # Makes prettier plots
	have_seaborn = True
except ImportError:
	have_seaborn = False

# Import other parts of the project
from popclasses import * # Import custom classes
from constants import model_constants # Import model constants
from environment import * # Import environment model


timeseries = False

def iterate_population(k,population,constants,t,R,P,A,B):
	for j in np.arange(constants.generations):
		# Start timer
		start = time.clock()

		for i in range(constants.L):

			E, C = environment(t,R,P,A,B)
			population.react(E,C)
			t = t+1

		population.breed_constant()
		population.react(E,C,1)


		if timeseries:
			plt.figure()
			animals = population.animals()
			genes = list(map(lambda x: x.genes, animals))
			data = pd.DataFrame(genes)
		
			if have_seaborn:
				sns.violinplot(data)
			else:
				data.boxplot()
		
			plt.ylim(-2,2)
			plt.savefig('timeseries/pop'+str(k+1)+'_genes_'+str(j+1)+'.png')
			plt.close()


		print("Pop {2}: Generation {0} of {1} done!".format(j+1,constants.generations,k+1))
		end = time.clock()
		print("Computation time: {0:.3e} s\n".format(end-start))


	I0, b, I0p, bp = [], [], [], []
	for animal in population.animals():
		I0.append(animal.genes['I0'])
		b.append(animal.genes['b'])
		I0p.append(animal.genes['I0p'])
		bp.append(animal.genes['bp'])

	I0, b = np.array(I0), np.array(b)

	C = np.linspace(-1,1,200)


	plt.figure()
	plt.plot(C,np.mean(I0)+np.mean(b)*C)
	plt.plot(C,np.mean(I0p)+np.mean(bp)*C)
	plt.savefig('pop'+str(k+1)+'_mean.png')

	plt.figure()
	animals = population.animals()
	genes = list(map(lambda x: x.genes, animals))
	data = pd.DataFrame(genes)
		
	if have_seaborn:
		sns.violinplot(data)
	else:
		data.boxplot()

	plt.ylim(-2,2)
	plt.savefig('pop'+str(k+1)+'_finalgenes.png')
	plt.close()



if __name__ == '__main__':
#def main():
	if have_seaborn:
		sns.set_palette("deep", desat=.6)
		sns.set_context(rc={"figure.figsize": (10, 7.5)})

	#pool = ThreadPool(processes=2)

	#################################
	############# START #############
	#################################


	# Get model constants
	constants = model_constants()

	# Now lets create a population of population_size animals that already have the correct random genes:
	animal_list = [Animal() for _ in range(constants.population_size)]

	# create a Population from animal_list
	population = Population(constants.population_size,animal_list)

	# set some variable model parameters:
	t, R, P, A, B = 0, 100, 0, 1, 0

	processes = range(1)


	plt.figure()
	t0 = np.arange(0,R*100,float(R)/10)
	env = np.array(list(map(lambda x: environment(x,R,P,A,B),t0)))
	plt.plot(t0,env[:,0],label='E')
	plt.plot(t0,env[:,1],'.',label='C')
	plt.legend()
	plt.savefig('environment.png')

	plt.figure()
	plt.hist(env[:,1],bins=100)
	plt.savefig('cues.png')
	
	mainfun = lambda k: iterate_population(k,population,constants,t,R,P,A,B)
	map(mainfun, processes)

#profile.run("main()")
