'''
Created on Sep 20, 2015

@author: mcasadevall
'''

from dynipd.allocation import Allocation

class AllocationServerSide(Allocation):
    '''Server side implementation of Allocation management'''

    def __init__(self, ip_range, network_block, machine, datastore):
        super().__init__(ip_range)
        self._datastore = datastore
        self._network_block = network_block

    def mark_ip_as_reserved(self):
        '''Moves an IP from unused to reserved'''
        raise NotImplementedError('Must be subclassed')

    def move_ip_to_standby(self):
        '''Moves an IP to standby status'''
        raise NotImplementedError('Must be subclassed')

    def move_ip_as_utilized(self):
        '''Moves an IP to standby status'''
        raise NotImplementedError('Must be subclassed')

    def return_ip_to_standby(self):
        '''Returns an IP to standby if its not being used'''
        raise NotImplementedError('Must be subclassed')

    def return_ip_to_unused(self):
        '''Returns an IP to unused'''
        raise NotImplementedError('Must be subclassed')
