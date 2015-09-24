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
        '''Assoicates an allocation with this Machine object'''

        # Connect this allocation to this machine
        self._datastore.assign_new_allocation(self, ip_allocation)

        # FIXME, make sure we don't add an allocation twice
        self._allocations.append(ip_allocation)

