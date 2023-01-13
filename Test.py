import unittest
from Event import Event
from Environment import Environment
from Source import Source, TestLoadBalancer 
from Request import Request
from Server import Server

class TestValue:
    def __init__(self, val):
        self.val = val
    
    def add(self, other):
        self.val+=other

class EventTest(unittest.TestCase):
    def testExecutionMethod(self):
        a = TestValue(1)
        method = lambda: a.add(1)
        e = Event(10, method)
        e.execute()
        self.assertEqual(a.val, 2)

    def testAlreadyTriggered(self):
        a = TestValue(1)
        method = lambda: a.add(1)
        e = Event(10, method)
        e.execute()
        e.execute()
        self.assertTrue(e.isTriggered, 2)
        self.assertEqual(a.val, 2)

class  EnvironmentTest(unittest.TestCase):
    def testExecutionOrder(self):
        a = []
        e1 = Event(3, lambda: a.append(2))
        e2 = Event(2, lambda: a.append(1))
        env = Environment(stopTime=10)
        env.scheduleEvent(e1)
        env.scheduleEvent(e2)
        env.run()
        self.assertEqual(a[0],1)
        self.assertEqual(a[1],2)
    
    def testLogData(self):
        env = Environment(stopTime=10)
        e1 = Event(3, lambda: env.logData("test", 2))
        env.scheduleEvent(e1)
        e2 = Event(2, lambda: env.logData("test", 1))
        env.scheduleEvent(e2)
        env.run()
        self.assertListEqual(env.log["test"], [1,2]) #test correct order
        self.assertListEqual(env.logTime["test"], [2,3]) #test correct timestamps

class SourceTest(unittest.TestCase):
    def testEventScheduling(self):
        stopTime = 10
        samplingInterval = 0.1
        env = Environment(stopTime=stopTime)
        loadBalancer = TestLoadBalancer()
        source = Source(samplingInterval, 0.5, [(0.5,1,1,10),(0.5,2,2,10)], loadBalancer, env)
        source.scheduleNextSampleEvent()
        env.run(debug=True)
        nSamples = len(env.log["sampleEvent"])
        self.assertEqual(nSamples, stopTime/samplingInterval) #number of sample events should be stopTime/samplingInterval

    def testArrivalSampling(self):
        stopTime = 10
        samplingInterval = 0.1
        env = Environment(stopTime=stopTime)
        loadBalancer = TestLoadBalancer()
        requestProb = 0.5
        source = Source(samplingInterval, requestProb, [(0.5,1,1,10),(0.5,2,2,10)], loadBalancer, env)
        source.scheduleNextSampleEvent()
        env.run(debug=True)
        nSamples = len(env.log["sampleEvent"])
        nArrival = len(env.log["arrivalEvent"])
        print(nSamples, nArrival)
        print(nArrival/nSamples)
        self.assertAlmostEqual(nArrival/nSamples, requestProb, delta=0.1) #test sample prob of arrival approximately equal to provided requestProb

    #def testRequestTypeSampling(self):

class ServerTest(unittest.TestCase):
    def testServer(self):
        env = Environment(stopTime=10)
        server = Server(environment = env)

        for i in range(10): #assign 10 requests to the server, should be all finished within the time limit
            req = Request(0, 1, 10, env)
            env.scheduleEvent(Event(0, lambda: server.assignRequest(req)))
            print(len(env.eventQueue))
        
        print(len(env.eventQueue))
        env.run(debug=True)
        self.assertEqual(len(server.queue), 0)
        self.assertEqual(len(env.log["requestProcessed"]), 10)

class RequestTest(unittest.TestCase):
    def testCancel(self):
        env = Environment(stopTime=10)
        req = Request(0, 1, 10, env) #request gets cancelled after 10 seconds
        env.run(debug=True)
        print(env.log['requestCancelled'])
        self.assertTrue(req.isCancelled)

    def testFinishprocessing(self):
        env = Environment(stopTime=10)
        server = Server(environment = env)
        req = Request(0, 1, 10, env) #request gets cancelled after 10 seconds, duration 1 sec
        req.assignToServer(server)
        req.startProcessing()
        env.run(debug=True)
        print(env.log['requestProcessed'])
        self.assertFalse(req.isCancelled)
        self.assertTrue(req.isProcessed)

    
if __name__ == '__main__':
    unittest.main()
    
