import unittest

import Mariana.layers as ML
import Mariana.initializations as MI
import Mariana.decorators as MD
import Mariana.costs as MC
import Mariana.regularizations as MR
import Mariana.scenari as MS
import Mariana.activations as MA

import theano.tensor as tt
import numpy

class MLPTests(unittest.TestCase):

	def setUp(self) :
		self.xor_ins = [
			[0, 0],
			[0, 1],
			[1, 0],
			[1, 1]
		]

		self.xor_outs = [0, 1, 1, 0]

	def tearDown(self) :
		pass

	def trainMLP_xor(self) :
		ls = MS.GradientDescent(lr = 0.1)
		cost = MC.NegativeLogLikelihood()

		i = ML.Input(2, 'inp')
		h = ML.Hidden(10, activation = MA.ReLU(), regularizations = [MR.L1(0), MR.L2(0)], name = "Hidden_0.500705866892")
		o = ML.SoftmaxClassifier(2, learningScenario = ls, costObject = cost, name = "out")

		mlp = i > h > o
		
		self.xor_ins = numpy.array(self.xor_ins)
		self.xor_outs = numpy.array(self.xor_outs)
		for i in xrange(1000) :
			mlp.train(o, inp = self.xor_ins, targets = self.xor_outs )

		return mlp

	# @unittest.skip("skipping")
	def test_xor(self) :
		mlp = self.trainMLP_xor()
		o = mlp.outputs.values()[0]

		pa = mlp.predictionAccuracy(o, inp = self.xor_ins, targets = self.xor_outs )["accuracy"]
		self.assertEqual(pa, 1)
		pc = mlp.classificationAccuracy(o, inp = self.xor_ins, targets = self.xor_outs )["accuracy"]
		self.assertEqual(pc, 1)
		
		self.assertEqual(mlp.classify( o, inp = [ self.xor_ins[0] ] )["class"], 0 )
		self.assertEqual(mlp.classify( o, inp = [ self.xor_ins[1] ] )["class"], 1 )
		self.assertEqual(mlp.classify( o, inp = [ self.xor_ins[2] ] )["class"], 1 )
		self.assertEqual(mlp.classify( o, inp = [ self.xor_ins[3] ] )["class"], 0 )

	# @unittest.skip("skipping")
	def test_save_load_pickle(self) :
		import cPickle, os, numpy
		import Mariana.network as MN

		mlp = self.trainMLP_xor()
		mlp.save("test_save")
		mlp2 = MN.loadModel("test_save.mar.mdl.pkl")
		
		o = mlp.outputs.values()[0]
		
		v1 = mlp.propagate( o.name, inp = self.xor_ins )["outputs"]
		v2 = mlp2.propagate( o.name, inp = self.xor_ins )["outputs"]
		self.assertEqual(numpy.sum(v1), numpy.sum(v2))
		
		os.remove('test_save.mar.mdl.pkl')

	# @unittest.skip("skipping")
	def test_ae(self) :

		data = []
		for i in xrange(8) :
			zeros = numpy.zeros(8)
			zeros[i] = 1
			data.append(zeros)

		ls = MS.GradientDescent(lr = 0.1)
		cost = MC.MeanSquaredError()

		i = ML.Input(8, name = 'inp')
		h = ML.Hidden(3, activation = MA.ReLU(), name = "hid")
		o = ML.Regression(8, activation = MA.ReLU(), learningScenario = ls, costObject = cost, name = "out" )

		ae = i > h > o

		miniBatchSize = 2
		for e in xrange(2000) :
			for i in xrange(0, len(data), miniBatchSize) :
				ae.train(o, inp = data[i:i+miniBatchSize], targets = data[i:i+miniBatchSize] )

		res = ae.propagate(o, inp = data)["outputs"]
		for i in xrange(len(res)) :
			self.assertEqual( numpy.argmax(data[i]), numpy.argmax(res[i]))

	# @unittest.skip("skipping")
	def test_composite(self) :
		ls = MS.GradientDescent(lr = 0.1)
		cost = MC.NegativeLogLikelihood()

		inp = ML.Input(2, 'inp')
		h1 = ML.Hidden(5, activation = MA.Tanh(), name = "h1")
		h2 = ML.Hidden(5, activation = MA.Tanh(), name = "h2")
		o = ML.SoftmaxClassifier(2, learningScenario = ls, costObject = cost, name = "out")
		c = ML.Composite(name = "Comp")

		inp > h1 > c
		inp > h2 > c
		mlp = c > o

		for i in xrange(10000) :
			ii = i%len(self.xor_ins)
			mlp.train(o, inp = [ self.xor_ins[ ii ] ], targets = [ self.xor_outs[ ii ] ])

		self.assertEqual(mlp.predict( o, inp = [ self.xor_ins[0] ] )["class"], 0 )
		self.assertEqual(mlp.predict( o, inp = [ self.xor_ins[1] ] )["class"], 1 )
		self.assertEqual(mlp.predict( o, inp = [ self.xor_ins[2] ] )["class"], 1 )
		self.assertEqual(mlp.predict( o, inp = [ self.xor_ins[3] ] )["class"], 0 )


	# @unittest.skip("skipping")
	def test_multiinputs(self) :
		ls = MS.GradientDescent(lr = 0.1)

		inpA = ML.Embedding(2, 2, 2, name="IA")
		inpB = ML.Input(2, name="IB")
		inpNexus = ML.Composite(name = "InputNexus")

		h1 = ML.Hidden(32, activation = MA.ReLU(), decorators = [], regularizations = [], name = "Fully-connected1" )
		
		o = ML.Regression(2,
			decorators = [],
			activation=MA.ReLU(),
			learningScenario = ls,
			costObject = MC.CrossEntropy(),
			name = "Out",
			regularizations = []
		)

		inpA > inpNexus
		inpB > inpNexus
		m = inpNexus > h1 > o
		m.init()

	# @unittest.skip("skipping")
	def test_embedding(self) :
		"""the first 3 and the last 3 should be diametrically opposed"""
		data = [[0], [1], [2], [3], [4], [5]]
		targets = [0, 0, 0, 1, 1, 1]

		ls = MS.GradientDescent(lr = 0.5)
		cost = MC.NegativeLogLikelihood()

		emb = ML.Embedding(1, 2, len(data), learningScenario = ls, name="emb")
		o = ML.SoftmaxClassifier(2, learningScenario = MS.Fixed(), costObject = cost, name = "out")
		net = emb > o
		
		miniBatchSize = 2
		for i in xrange(2000) :
			for i in xrange(0, len(data), miniBatchSize) :
				net.train(o, emb=data[i:i+miniBatchSize], targets=targets[i:i+miniBatchSize])
		
		embeddings = emb.getEmbeddings()
		for i in xrange(0, len(data)/2) :
			v = numpy.dot(embeddings[i], embeddings[i+len(data)/2])
			self.assertTrue(v < -1)

	# @unittest.skip("skipping")
	def test_conv(self) :
		import Mariana.convolution as MCONV
		import theano

		def getModel(inpSize, filterWidth) :
			ls = MS.GradientDescent(lr = 0.5)
			cost = MC.NegativeLogLikelihood()
			
			pooler = MCONV.MaxPooling2D(1, 2)

			i = ML.Input(inpSize, name = 'inp')
			ichan = MCONV.InputChanneler(1, inpSize, name = 'inpChan')
			
			c1 = MCONV.Convolution2D( 
				nbFilters = 5,
				filterHeight = 1,
				filterWidth = filterWidth,
				activation = MA.ReLU(),
				pooler = pooler,
				name = "conv1"
			)

			c2 = MCONV.Convolution2D( 
				nbFilters = 10,
				filterHeight = 1,
				filterWidth = filterWidth,
				activation = MA.ReLU(),
				pooler = pooler,
				name = "conv2"
			)

			f = MCONV.Flatten(name = "flat")
			h = ML.Hidden(5, activation = MA.ReLU(), decorators = [], regularizations = [ ], name = "hid" )
			o = ML.SoftmaxClassifier(2, decorators = [], learningScenario = ls, costObject = cost, name = "out", regularizations = [ ] )
			
			model = i > ichan > c1 > c2 > f > h > o
			return model

		def makeDataset(nbExamples, size, patternSize) :
			data = numpy.random.randn(nbExamples, size).astype(theano.config.floatX)
			data = data / numpy.sum(data)
			pattern = numpy.ones(patternSize)
			
			targets = []
			for i in xrange(len(data)) :
				if i%2 == 0 :
					start = numpy.random.randint(0, size/2 - patternSize)
					targets.append(0)
				else :
					start = numpy.random.randint(size/2, size - patternSize)
					targets.append(1)

				data[i][start:start+patternSize] = pattern

			targets = numpy.asarray(targets, dtype=theano.config.floatX)
			
			trainData, trainTargets = data, targets

			return (trainData, trainTargets)

		examples, targets = makeDataset(1000, 128, 6)
		model = getModel(128, 3)
		miniBatchSize = 32
		for epoch in xrange(100) :
			for i in xrange(0, len(examples), miniBatchSize) :
				res = model.train("out", inp = examples[i : i +miniBatchSize], targets = targets[i : i +miniBatchSize] )
		
		self.assertTrue(res["score"] < 0.1)

if __name__ == '__main__' :
	import Mariana.settings as MSET
	MSET.VERBOSE = False
	unittest.main()
