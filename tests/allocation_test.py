'''
Created on Sep 24, 2015

@author: mcasadevall
'''
import unittest


from dynipd.server.allocation import Allocation

class TestAllocation(unittest.TestCase):
    '''Tests base class Allocation's methods'''

    def test_equal_comparsion(self):
        '''Confirms two Allocations match each other'''
        allocation1 = Allocation('192.0.2.1/32')
        allocation2 = Allocation('192.0.2.1/32')

        self.assertEqual((allocation1 == allocation2), True, 'Same allocations do not match!')

    def test_not_equal_comparsion(self):
        '''Confirms two Allocations do not match each other'''
        allocation1 = Allocation('192.0.2.1/32')
        allocation2 = Allocation('192.0.2.2/32')

        self.assertEqual((allocation1 == allocation2), False, 'Different allocations match!')

    def test_is_empty(self):
        '''Tests that an allocation reports empty if there are no used IPs'''
        allocation = Allocation('192.0.2.1/32')
        self.assertEqual(allocation.is_empty(), True, 'Allocation falsely reported its fulL!')

        # Now stick an IP and try again
        next_ip = allocation.get_unused_ip()
        allocation.mark_ip_as_reserved(next_ip)

        self.assertEqual(allocation.is_empty(), False, 'Allocation falsely reports its empty')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
