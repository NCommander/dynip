'''
Created on Sep 20, 2015

@author: mcasadevall
'''

import ipaddress
from socket import AF_INET, AF_INET6
from dynipd.validation import ValidationAndNormlization as check

class NetworkBlock(object):
    '''A NetworkBlock represents an object from the network_topologies table

    NetworkBlocks are made up of Allocations(), the size of which is defined by the allocation_size
    parameter. The NetworkBlock keeps track of the total amount of allocations, generates new
    Allocations() as necessary, and does sanity checking to make sure the state doesn't get in.

    Internally, all allocations are kept in a dict, with the dict being the location within
    a block. For example, if we're managing 192.0.2.0/24, with an allocation size of 32
    (one IP), that gives us a total of 254 valid allocations (the and network broadcast
    address requires special handling). If a client gets IP 192.0.2.124, that's stored
    as allocation[124]. This allows us to not keep unallocated blocks in memory (if we
    were doing IPv6 allocations,  a /48 has 65565 valid /64 blocks!)
    '''

    def __init__(self, network_dict):
        '''Python representation of a network block

        Raises:
            ValueError - if a network block has invalid information'''

        self._network_block_utilization = {}
        self._next_allocation = 0

        self.network_id = network_dict['id']
        self.network_name = network_dict['name']
        self.family = network_dict['protocol']
        self.location = network_dict['location']
        self.network = ipaddress.ip_network(network_dict['network'], strict=True)
        self.allocation_size = network_dict['allocation_size']
        self.reserved_blocks = network_dict['reserved_blocks']

        # Sanity check ourselves
        check.is_valid_ip_family(self.family)

        # Work out some values based on family size, and make sure our allocation is sane
        if self.family == AF_INET:
            if self.allocation_size > 32 or self.allocation_size < self.network.prefixlen:
                raise ValueError('Allocation prefix size is too large!')

        if self.family == AF_INET6:
            if self.allocation_size > 128 or self.allocation_size < self.network.prefixlen:
                raise ValueError('Allocation prefix size is too large!')

        # We can calculate the number of hosts by doing powers of 2 math
        self._total_number_of_allocations = 2**(self.allocation_size-self.network.prefixlen)

        # In all cases, we need to handle the network address
        self._mark_network_address()

        # If we're IPv4, we need handle the broadcast address
        if self.family == AF_INET:
            self._mark_broadcast_address()

    def _mark_network_address(self):
        '''Marks the network address in an _allocation'''

        # The network address is always the first one of a block so ...
        self._network_block_utilization.update({0 : 'NETWORK_ADDRESS'})
        self._next_allocation += 1

    # pylint: disable=line-too-long
    def _mark_broadcast_address(self):
        '''Removes the broadcast address out of the network block dict'''
        # The broadcast address is top of the block
        self._network_block_utilization.update({self._total_number_of_allocations : 'BROADCAST_ADDRESS'})

