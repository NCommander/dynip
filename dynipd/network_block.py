'''
Created on Sep 20, 2015

@author: mcasadevall
'''

import ipaddress
from socket import AF_INET, AF_INET6
from dynipd.validation import ValidationAndNormlization as check
from dynipd.server.allocation import AllocationServerSide

class NetworkBlockFull(Exception):
    '''A NetworkBlock is out of allocations to hand out'''
    def __init__(self, value):
        super(NetworkBlockFull, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class AllocationNotFound(Exception):
    '''The Allocation requested was not found'''
    def __init__(self, value):
        super(AllocationNotFound, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class NetworkBlock(object):
    '''A NetworkBlock represents an object from the network_topologies table

    NetworkBlocks are made up of Allocations(), the size of which is defined by the allocation_size
    parameter. The NetworkBlock keeps track of the total amount of allocations, generates new
    Allocations() as necessary, and does sanity checking to make sure the state doesn't get in.

    Internally, all allocations are kept in a dict, with the dict being the location within
    a block. For example, if we're managing 192.0.2.0/24, with an allocation size of 32
    (one IP), that gives us a total of 254 valid allocations (the and _network broadcast
    address requires special handling). If a client gets IP 192.0.2.124, that's stored
    as allocation[124]. This allows us to not keep unallocated blocks in memory (if we
    were doing IPv6 allocations,  a /48 has 65565 valid /64 blocks!)
    '''

    def __init__(self, network_dict, datastore):
        '''Python representation of a _network block

        Raises:
            ValueError - if a _network block has invalid information'''

        self.datastore = datastore
        self._network_block_utilization = {}

        self._network_id = network_dict['id']
        self.network_name = network_dict['name']
        self.family = network_dict['family']
        self.location = network_dict['location']
        self._network = ipaddress.ip_network(network_dict['network'], strict=True)
        self.allocation_size = network_dict['allocation_size']
        self.reserved_blocks = network_dict['reserved_blocks']

        # Sanity check ourselves
        check.is_valid_ip_family(self.family)

        # Work out some values based on family size, and make sure our allocation is sane
        total_length_of_an_ip = None
        if self.family == AF_INET:
            total_length_of_an_ip = 32
            if self.allocation_size > 32 or self.allocation_size < self._network.prefixlen:
                raise ValueError('Allocation prefix size is too large!')

        if self.family == AF_INET6:
            total_length_of_an_ip = 128
            if self.allocation_size > 128 or self.allocation_size < self._network.prefixlen:
                raise ValueError('Allocation prefix size is too large!')

        # We can calculate the number of hosts by doing powers of 2 math
        self._total_number_of_allocations = 2**(self.allocation_size-self._network.prefixlen)

        # Now the tricky bit. We need to know (in binary), how much we need to add to get
        # the next IP range we're allocation.

        # Clarity note, if we're allocating single IPs, the following equation will be 0. Anything
        # raised to 0 becomes 1.
        self._block_seperator = 2**(total_length_of_an_ip-self.allocation_size)

        # Depending on the size of the block, and our family, there are some allocations
        # that aren't valid. If we're handing out /32 addresses, we need to take in account
        # that the _network address and broadcast address of a block are unusable. Allocation
        # handles this case for >/32 blocks, but we need to handle it here otherwise.

        # FIXME: Confirm this logic is sane ...

        # IP ranges are 0-255. Powers of two math gets us 256, so drop it by one so everything
        # else ends up in the right ranges
        self._total_number_of_allocations -= 1

        # In all cases, we need to handle the _network address
        self._mark_network_address()

        # If we're IPv4, we need handle the broadcast address
        if self.family == AF_INET:
            self._mark_broadcast_address()

    def __eq__(self, other):
        '''Compares two different NetworkBlocks'''
        if self.get_id() == other.get_id():
            return True

        return False

    def get_id(self):
        '''Returns database ID number'''
        return self._network_id

    def get_name(self):
        '''Returns the name of this _network'''
        return self.network_name

    def create_new_allocation(self, machine):
        '''Creates a new allocation and assigns it to a machine'''
        new_allocation = self._get_new_allocation(machine)
        self.datastore.assign_new_allocation(machine, new_allocation)
        return new_allocation

    def _get_new_allocation(self, machine):
        '''Retrieves the next allocation available for a machine'''

        # Find the next open IP by walking the struct for the first gap
        next_allocation = None

        for pointer in range(0, self._total_number_of_allocations):
            if not pointer in self._network_block_utilization:
                next_allocation = pointer
                break

        # If we can't get an allocation, the block is full, raise an error
        if not next_allocation:
            raise NetworkBlockFull('No more allocations open in this block')

        # Internally, _network_block_utilization is essentially an offset; the 0 block is
        # the _network address, then the start of the next allocation is _block_seperator
        # (which is the size of an allocation as an integer) * next allocation

        # Knowing that, calculating next_address and next_network is easy
        next_address = self._network.network_address + self._block_seperator*next_allocation
        next_network = ipaddress.ip_network(('%s/%s') % (next_address, self.allocation_size))

        unusued_allocation = AllocationServerSide(next_network, self, machine, self.datastore)
        self._network_block_utilization.update({pointer: unusued_allocation})

        # Assoicate the allocation with a machine
        machine.add_allocation(unusued_allocation)
        return unusued_allocation


    def _mark_network_address(self):
        '''Marks the _network address in an _allocation'''

        # The _network address is always the first one of a block so ...
        self._network_block_utilization.update({0 : 'NETWORK_ADDRESS'})

    # pylint: disable=line-too-long
    def _mark_broadcast_address(self):
        '''Removes the broadcast address out of the _network block dict'''
        # The broadcast address is top of the block
        self._network_block_utilization.update({self._total_number_of_allocations : 'BROADCAST_ADDRESS'})

    def _get_allocation_offset(self, cidr_block):
        '''Gets the offset within the dict for a given allocation'''

        # Validate our input
        ip_network = check.validate_ip_network(cidr_block)
        if not check.do_cidr_blocks_overlap(self._network, cidr_block):
            raise ValueError('Allocation block not within NetworkBlock')
        if ip_network.prefixlen != self.allocation_size:
            raise ValueError('Allocation block has wrong allocation size')

        # Offset is calculated by the difference in network addresses
        offset = int(ip_network.network_address)-int(self._network.network_address)

        import pprint
        pprint.pprint(offset)
        pprint.pprint(self._network_block_utilization)
        # Confirm it exists, or throw a ValueError
        if offset in self._network_block_utilization:
            return offset

        raise AllocationNotFound("Allocation doesn't exist within NetworkBlock")

    def _remove_allocation_assoication(self, ip_allocation):
        '''Deletes an allocation'''

        # Sanity check our arguments
        if not isinstance(ip_allocation, AllocationServerSide):
            raise ValueError('ip_allocation must be AllocationServerSide')

        # _get_allocation_offset will sanity check the input for us
        offset = self._get_allocation_offset(ip_allocation.get_allocation_cidr())
        self._network_block_utilization.pop(offset)
