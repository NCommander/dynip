'''
Created on Sep 20, 2015

@author: mcasadevall
'''

class NetworkBlock(object):
    def __init__(self, network_dict):
        '''Python representation of a network block'''
        self.network_id = network_dict['id']
        self.protocol = network_dict['protocol']
        self.location = network_dict['location']
        self.network = network_dict['network']
        self.allocation_size = network_dict['allocation_size']
        self.reserved_blocks = network_dict['reserved_blocks']
