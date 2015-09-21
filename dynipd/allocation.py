'''
Created on Sep 19, 2015

@author: mcasadevall
'''

class Allocation(object):
    '''An allocation is a block of IP or IPs that a machine can use'''

    def __init__(self, ip_range):
        '''Create a new allocation based on this range'''

    def get_status(self):
        '''Reports the status of all IPs within a block'''

    def get_usage(self):
        '''Reports current status of IPs within an allocation'''

    def mark_ip_as_utilized(self):
        '''Marks an IP as utilized'''

    def return_ip_to_standby(self):
        '''Returns an IP to standby if its not being used'''
