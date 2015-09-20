'''
Created on Sep 20, 2015

@author: mcasadevall
'''

import ipaddress
from socket import AF_INET, AF_INET6

class NetworkBlock(object):
    def __init__(self, network_dict):
        '''Python representation of a network block

        Raises:
            ValueError - if a network block has invalid information'''

        self.network_id = network_dict['id']
        self.family = network_dict['protocol']
        self.location = network_dict['location']
        self.network = ipaddress.ip_network(network_dict['network'], strict=True)
        self.allocation_size = network_dict['allocation_size']
        self.reserved_blocks = network_dict['reserved_blocks']

        network_prefix = self.network.prefixlen
        length_of_ip = 0
        # Work out some values based on family size, and make sure our allocation is sane
        if self.family == AF_INET:
            length_of_ip = 32
            import pprint
            pprint.pprint(self.allocation_size)
            if self.allocation_size > 32 or self.allocation_size < network_prefix:
                raise ValueError('Allocation prefix size is too large!')

        if self.family == AF_INET6:
            length_of_ip = 128
            if self.allocation_size > 128 or self.allocation_size < network_prefix:
                raise ValueError('Allocation prefix size is too large!')

        # We can calculate the number of hosts by doing powers of 2 math
        total_number_of_allocations = 2**(self.allocation_size-network_prefix)

        import pprint
        print(total_number_of_allocations)

def get_num_of_hosts(self):
    pass
