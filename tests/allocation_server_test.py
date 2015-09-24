'''
Created on Sep 20, 2015

@author: mcasadevall
'''
import unittest
from dynipd.allocation import Allocation

class AllocationServerSideTest(unittest.TestCase):
    '''Tests the AllocationServerSide class'''

    def testCreateIPv4Allocation(self):
        '''Creates a basic IPv4 allocation'''
        a=Allocation('192.0.2.32/27')
        a.get_usage()

    def testCreateIPv6Allocation(self):
        '''Creates a basic IPv6 allocation'''
        Allocation('fd00:a3b1:78a2::/64')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
