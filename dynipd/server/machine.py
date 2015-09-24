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

    def remove_allocation(self, ip_allocation, fatal=True):
        '''Removes an allocation associates with this machine'''

        try:
            allocation_idx = self._allocations.index(ip_allocation)
        except ValueError:
            # If we're OK with non-fatal, return false, else re-raise
            if fatal:
                return False
            else:
                raise ValueError('Allocation not associated with this machine')


        # Attempt to delete allocation; a sanity check will cause to this to fail
        # if there are any open IP allocations
        allocation = self._allocations[allocation_idx]
        self._datastore.remove_allocation_assignment(allocation)

        