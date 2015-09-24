'''
Created on Sep 20, 2015

@author: mcasadevall
'''

import ipaddress
from dynipd.allocation import Allocation
from dynipd.validation import ValidationAndNormlization as check

class AllocationServerSide(Allocation):
    '''Server side implementation of Allocation management'''

    def __init__(self, ip_range, network_block, machine, datastore):
        super().__init__(ip_range)
        self._datastore = datastore
        self._network_block = network_block
        self._machine = machine

    def mark_ip_as_reserved(self, ip_to_reserve):
        '''Moves an IP from unused to reserved'''

        # Check that this is a valid IP for this allocation
        ip_address = ipaddress.ip_address(ip_to_reserve)
        if not check.is_ip_within_block(ip_address, self._allocation):
            raise ValueError('ip_address not within allocation')

        if not self._confirm_ip_is_unused(ip_address):
            raise ValueError(('%s is not UNALLOCATED' % (str(ip_address),) ))

        # We're good, create the allocation
        offset = int(ip_address)-int(self._allocation_start)

        ip_status = {}
        ip_status['status'] = 'RESERVED'
        ip_status['reserved_until'] = None
        self._allocation_utilization.update({offset: ip_status})

        import pprint
        pprint.pprint(self._machine)
        # Now update the database with our reservation
        self._datastore.set_ip_status(ip_address, 'RESERVED', self, self._machine)

    def move_ip_to_standby(self, ip_address):
        '''Moves an IP to standby status'''
        raise NotImplementedError('Must be subclassed')

    def move_ip_as_utilized(self, ip_address):
        '''Moves an IP to standby status'''
        raise NotImplementedError('Must be subclassed')

    def return_ip_to_standby(self, ip_address):
        '''Returns an IP to standby if its not being used'''
        raise NotImplementedError('Must be subclassed')

    def return_ip_to_unused(self, ip_address):
        '''Returns an IP to unused'''
        raise NotImplementedError('Must be subclassed')
