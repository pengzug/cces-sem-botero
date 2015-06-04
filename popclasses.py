import numbers # To check if a type is numeric
import numpy as np
import time
from copy import deepcopy
from constants import model_constants # Import model constants

# Implement classes

# Takes a list of seven numbers as input and outputs a dictionary containing the corresponding genes.
class Genome(dict):
    def __init__(self,lst):
        super(Genome,self).__init__()
        if ((len(lst) == 7) & (all(isinstance(x,numbers.Number) for x in lst))):
            self['h'] = lst[0]
            self['s'] = lst[1]
            self['a'] = lst[2]
            self['I0'] = lst[3]
            self['I0p'] = lst[4]
            self['b'] = lst[5]
            self['bp'] = lst[6]
            self._constants = model_constants()
        else:
            raise TypeError('Argument must be a list of 7 numbers.')

    def mutate(self):
        mu = self._constants["mu"]

        for gene in ['h','s','I0','I0p']:
            r = np.random.rand()
            if (r<=mu):
                mutation_step = np.random.normal(loc=0,scale=0.05)
                self[gene] = self[gene] + mutation_step

        if (self['s'] > 0.5):
            for gene in ['a','b','bp']:
                r = np.random.rand()
                if (r<=mu):
                    mutation_step = np.random.normal(loc=0,scale=0.05)
                    self[gene] = self[gene] + mutation_step
        else:
            self['a'], self['b'], self['bp'] = 0, 0, 0

        return self



# Takes a Genome as input and outputs an Animal with traits genes, mismatch, adjustments and insulation.
class Animal:
    def __init__(self,*args):
        if (len(args) > 0):
            genes = args[0]
            if not isinstance(genes,Genome):
                raise TypeError('First argument must be of type Genome.')
        else:
            genes = self._random_genes()

        self.genes = genes
        self.mismatch = 0
        self.adjustments = 0
        self.insulation = genes['I0']
            

    def _random_genes(self):
        rand_numbers = np.random.rand(6) # create 6 random genes in the interval [0,1)
        rand_genes = np.concatenate(([1],[1,1,2,2,4,4]*rand_numbers+[0,0,-1,-1,-2,-2]))
        genes = Genome(rand_genes)

        if (genes['s']<=0.5):
            genes['a'], genes['b'], genes['bp'] = 0, 0, 0
        return genes


# Takes a population size and a list of Animal as input and delivers a Population.
class Population:
    # Constructor of the population
    def __init__(self,size,animals):
        if (isinstance(size,int) & (all(isinstance(x,Animal) for x in animals))):
            if (size == len(animals)):
                self._animals = np.array(animals)
                self._size = size
                self._constants = model_constants()
            else:
                raise ValueError('The size parameter must be equal to the length of the list of animals.')
        else:
            raise TypeError('First argument must be of type int, second of type list of Animal.')

    # Outputs the ndarray of Animal 
    def animals(self):
        return self._animals

    # Outputs the current size of the population
    def size(self):
        return self._size

    # Calculates the insulation of each Animal in the Population based on cue C and environment E
    def react(self,E,C,evolve_all=False):
        new_animals = self._animals

        for animal in new_animals:
            r = np.random.rand()
            if ((r <= animal.genes['a']) | evolve_all):
                r = np.random.rand()
                if (r <= animal.genes['h']):
                    new_insulation = animal.genes['I0']+animal.genes['b']*C
                else:
                    new_insulation = animal.genes['I0p']+animal.genes['bp']*C
                animal.insulation = new_insulation
                animal.adjustments = animal.adjustments + 1
            animal.mismatch = animal.mismatch + np.abs(animal.insulation-E)
        self._animals = new_animals


    # Calculates the lifetime payoff of a single Animal animal.
    def _lifetime_payoff(self,animal):
        tau = self._constants["tau"]
        if (animal.genes['s'] <= 0.5):
            return np.exp(-tau*animal.mismatch)
        else:    
            return max(np.exp(-tau*animal.mismatch) - self._constants["kd"] - (animal.adjustments - 1)* self._constants["ka"], 0)

    def _max_payoff(self,animal):
        if (animal.genes['s'] <= 0.5):
            return 1
        else:
            return (1 - self._constants["kd"])

    # Iterates the entire Population to a new generation, calculating the number of offspring of each Animal.
    def breed_constant(self):
        calc_payoff = np.vectorize(self._lifetime_payoff)
        lifetime_payoff = calc_payoff(self._animals)
        mean_payoff = np.mean(lifetime_payoff)

        if (mean_payoff == 0):
            raise RuntimeError("Mean payoff of population decreased to 0. Check your parameters!")
        else:
            payoff_factor = lifetime_payoff/mean_payoff

        offspring = np.random.poisson(lam=payoff_factor)
        born_animals = np.repeat(self._animals,offspring)
        mutate_pop = np.vectorize(lambda x: Animal(x.genes.mutate()))
        new_animals = mutate_pop(born_animals)

        N = len(new_animals)
        print("Population size: {0}".format(N))
        if (N > self._constants["population_size"]):
            new_animals = np.random.choice(new_animals,self._constants["population_size"],replace=False)
        elif (N < self._constants["population_size"]):
            copy_clones = np.vectorize(deepcopy)
            clones = copy_clones(np.random.choice(new_animals,self._constants["population_size"] - N))
            new_animals = np.append(new_animals,clones)

        self._animals = new_animals


    def breed_variable(self,f3,j): 
        calc_payoff = np.vectorize(self._lifetime_payoff)
        lifetime_payoff = calc_payoff(self._animals)
        max_payoff = []
        for animal in (self._animals):
            max_payoff.append(self._max_payoff(animal))
        #max_payoff = 1        
        
        payoff_factor = lifetime_payoff/max_payoff
#        for r in range(self._constants["population_size"]):
#            if (payoff_factor[r] > 1):
#                print("Payoff Factor: {0}, Max Payoff: {1}".format(payoff_factor[r],max_payoff[r]))
#                payoff_factor[r] = 1
        q = self._constants["q"]
        payoff_factor = q*payoff_factor

        #print("Payoff Factor: {0}".format(payoff_factor))
        offspring = np.random.poisson(lam=payoff_factor)
        born_animals = np.repeat(self._animals,offspring)
        new_animals = []
        for animal in born_animals:
            animal.genes = animal.genes.mutate()
            new_animals.append(Animal(animal.genes))
#        mutate_pop = np.vectorize(lambda x: Animal(x.genes.mutate()))
#        new_animals = mutate_pop(born_animals)

        N = len(new_animals)
        print("Population size: {0}".format(N))
        mean_lifetime_payoff = np.mean(lifetime_payoff)
        print("Mean Lifetime Payoff: {0}".format(mean_lifetime_payoff))
        if (N == 0):
            f3.write(" died out in generation {0}\n".format(j))
            return 1, j
            
        #if (N > self._constants["population_size"]):
        if (N > 10000):
            new_animals = np.random.choice(new_animals,self._constants["population_size"],replace=False)

        self._animals = new_animals
        self._size = len(new_animals)
        
        return 0, 1000