'''
Created on Sep 19, 2015

@author: mcasadevall
'''

import ipaddress
from dynipd.validation import ValidationAndNormlization as check
from _socket import AF_INET, AF_INET6

class AllocationFull(Exception):
    '''An Allocation is out of allocations to hand out'''
    def __init__(self, value):
        super(AllocationFull, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class AllocationNotEmpty(Exception):
    '''An attempt was made to try and remove() an allocation with in use IPs'''
    def __init__(self, value):
        super(AllocationNotEmpty, self).__init__(value)
        self.value = value
    def __str__(self):
        return repr(self.value)

class Allocation(object):
    '''An _allocation is a block of IP or IPs that a machine can use'''

    def __init__(self, ip_range):
        '''Create a new _allocation based on this range'''
        self.allocation_id = None
        self._allocation_utilization = {}

        # _allocation_status refers to the status of a block as a whole. It is equal to the
        # highest status of any IP within a block
        self._allocation_status = 'UNALLOCATED'

        # Do the usual validation and sanity check
        self._allocation = check.confirm_valid_network(ipaddress.ip_network(ip_range, strict=True))
        self._allocation_start = self._allocation.network_address

        address_size = None
        if self._allocation.version == 4:
            address_size = 32
            self.family = AF_INET

        if self._allocation.version == 6:
            address_size = 128
            self.family = AF_INET6

        # Power of 2 math to the rescue; work out how many IPs we represent
        self._total_number_of_ip = 2**(address_size-self._allocation.prefixlen)
        self._available_ips = self._total_number_of_ip

        # The network address is unusable in IPv4, and for our sanity, mark it
        # unusable in IPv6 (dealing with b1oc:: as a valid IP is bleh)
        #
        # If we're IPv4, the  broadcast addresses is unusable within a block.
        if self._total_number_of_ip != 1:
            self._mark_network_address()

            if self.family == AF_INET:
                self._mark_broadcast_address()

    def __eq__(self, other):
        '''Tests if two allocations are equal'''

        # FIXME: this needs to be more indepth check

        # Currently allocations are equal if their CIDR range matches
        if self.get_allocation_cidr() == other.get_allocation_cidr():
            return True

        return False

    def remove(self):
        '''Deletes this allocation (this has to be subclassed to do anything useful)'''
        # A remove attempt is only valid if an allocation is empty
        if not self.is_empty():
            raise AllocationNotEmpty('An allocation must not have any IPs in use before remove()')

    def set_id(self, allocation_id):
        '''Sets the ID from the database to the object'''
        self.allocation_id = allocation_id

    def get_id(self):
        '''Returns stored database ID, or None if one hasn't been assigned'''
        return self.allocation_id

    def get_allocation_cidr(self):
        '''Returns string of the CIDR representation of the block'''
        return str(self._allocation)

    def get_unused_ip(self):
        '''Returns an unallocated IP from the allocation'''

        # Find the next open IP by walking the struct for the first gap
        next_ip = None

        for pointer in range(0, self._total_number_of_ip):
            if not pointer in self._allocation_utilization:
                next_ip = pointer
                break

        if next_ip == None: # Zero can be a valid offset
            raise AllocationFull('No unused IPs in block')

        # A little IP math later, and we have our address
        return self._allocation_start+next_ip

    def get_usage(self):
        '''Reports the status of all IPs within a block'''
        saner_dict = {}
        for ip_offset, status in sorted(self._allocation_utilization.items()):
            # Broadcast/Network are internal; we don't report them if they're in use.
            if status != 'BROADCAST_ADDRESS' or status != 'NETWORK_ADDRESS':
                saner_dict.update({(self._allocation_start+ip_offset): status})

        return saner_dict

    def is_empty(self):
        '''Reports if an allocation is empty'''
        if len(self.get_usage()):
            return False

        return True

    def mark_ip_as_reserved(self, ip_to_reserve):
        '''Moves an IP from unused to reserved'''
        # Check that this is a valid IP for this allocation
        ip_address = ipaddress.ip_address(ip_to_reserve)
        if not check.is_ip_within_block(ip_address, self._allocation):
            raise ValueError('ip_address not within allocation')

        if not self._confirm_ip_is_unused(ip_address):
            raise ValueError(('%s is not UNALLOCATED' % (str(ip_address),) ))

        # We're good, create the allocation
        offset = self._calculate_offset(ip_address)

        ip_status = {}
        ip_status['status'] = 'RESERVED'
        ip_status['reserved_until'] = None
        self._allocation_utilization.update({offset: ip_status})

        # We return the validated ip_address for postprocessing by the parent class
        return ip_address

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

    def _confirm_ip_is_unused(self, ip_address):
        '''Confirms an IP is unused within an allocation'''
        ip_address = ipaddress.ip_address(ip_address)

        offset = int(ip_address)-int(self._allocation_start)

        # if its not in the dict, its unused
        if not offset in self._allocation_utilization:
            return True

        return False

    def _mark_network_address(self):
        '''Marks the network address in an _allocation'''

        # The network address is always the first one of a block so ...
        self._allocation_utilization.update({0 : 'NETWORK_ADDRESS'})
        self._available_ips =- 1

    # pylint: disable=line-too-long
    def _mark_broadcast_address(self):
        '''Mark the broadcast address'''

        # The broadcast address is top of the block
        self._allocation_utilization.update({self._total_number_of_ip : 'BROADCAST_ADDRESS'})
        self._available_ips =- 1

    def _calculate_offset(self, ip_address):
        '''Returns the offset within the dict of a given IP'''
        return int(ip_address)-int(self._allocation_start)
