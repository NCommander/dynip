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

    def get_network_block(self):
        '''Returns the network block associated with this allocation'''
        return self._network_block

    def remove(self):
        '''Deletes this allocation'''
        super().remove()

        # Remove the allocation from the NetworkBlock and the Machine objects
        #
        # This is done via protected members as these functions only check that their arguments
        # are correct, not that the allocation is unused. Since we're in the same package, I'm
        # just overriding the protected-access war

        # pylint: disable=protected-access
        self._network_block._remove_allocation_assoication(self)
        self._machine._remove_allocation_assoication(self)
        # pylint: enable=protected-access

        # Remove us from the database
        self._datastore.remove_allocation_assignment(self)


    def mark_ip_as_reserved(self, ip_to_reserve):
        '''Marks an IP as used and updates the database'''
        ip_address = super().mark_ip_as_reserved(ip_to_reserve)

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
