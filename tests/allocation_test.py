'''
Created on Sep 24, 2015

@author: mcasadevall
'''
import unittest


from dynipd.server.allocation import Allocation

class TestAllocation(unittest.TestCase):
    '''Tests base class Allocation's methods'''

    def test_comparsion_true(self):
        '''Confirms two Allocations match each other'''
        allocation1 = Allocation('192.0.2.1/32')
        allocation2 = Allocation('192.0.2.1/32')

        self.assertEqual((allocation1 == allocation2), True, 'Same allocations do not match!')

    def test_not_equal(self):
        '''Confirms two Allocations do not match each other'''
        allocation1 = Allocation('192.0.2.1/32')
        allocation2 = Allocation('192.0.2.2/32')

        self.assertEqual((allocation1 == allocation2), False, 'Different allocations match!')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
