'''
Created on Sep 21, 2015

@author: mcasadevall
'''

class Machine(object):
    '''Represents a machine object'''

    def __init__(self, name, datastore):
        self._name = name
        self._datastore = datastore

        machine_dict = datastore.get_machine(self._name)
        self._id = machine_dict['id']
        self._token = machine_dict['token']

    def get_id(self):
        '''Gets the ID of the machine from the database'''
        return self._id

    def get_name(self):
        '''Returns the name of the machine'''
        return self._name
