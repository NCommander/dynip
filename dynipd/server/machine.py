'''
Created on Sep 21, 2015

@author: mcasadevall
'''

class Machine(object):
    '''Represents a machine object'''

    def __init__(self, name, datastore):
        self._name = name
        self._datastore = datastore
        self._allocations = []

        machine_dict = datastore.get_machine(self._name)
        self._id = machine_dict['id']
        self._token = machine_dict['token']

    def get_id(self):
        '''Gets the ID of the machine from the database'''
        return self._id

    def get_name(self):
        '''Returns the name of the machine'''
        return self._name

    def add_allocation(self, ip_allocation):
        '''Associates an allocation with this Machine object'''

        # Connect this allocation to this machine
        self._datastore.assign_new_allocation(self, ip_allocation)

        # FIXME, make sure we don't add an allocation twice
        self._allocations.append(ip_allocation)

    def list_allocations(self):
        '''Returns a copy of the allocations with this Machine'''
        return self._allocations.copy()

    def _remove_allocation_assoication(self, ip_allocation):
        '''Removes an allocation from the _allocation table. Called from Allocation.remove()'''
        try:
            allocation_idx = self._allocations.index(ip_allocation)
        except ValueError:
            # If we're OK with non-fatal, return false, else re-raise
            raise ValueError('Allocation not associated with this machine')

        # We unconditionally remove; we should only be called from Allocation.remove()
        # which handles safety checks
        self._allocations.pop(allocation_idx)

