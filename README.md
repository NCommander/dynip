# Overview

DynIP is a daemon to handle allocating static IPs for multihoming in the context of a hosting provider,
it's meant to ease configuration where IP setup needs changes rapidly and frequently. As such, DynIP works
on the basis of subdividing allocation in the form CIDR network blocks, and logical locations. As such,
DynIP operates with various pools of IPs.

# Terminology
For purposes of clarification, documentation for DynIP uses the following terms:

## Allocation States
A group of IPs used by DynIP is known as an allocation. As such 192.0.2.1/32 and 192.0.2.128/28 are
both allocations. Within a network block (for example 192.0.2.0/24), allocations are divided
into three different pools. To facility this, the overall network topology has is described in
the form of CIDR addresses which are tagged by location. An allocation can be as small as a single
IP.

Nodes actively track the usage of IPs within a block, and can automatically request a new allocation
should it be required. As part of this, DynIP automatically configures additional IPs on a given
network interface, performs gratuitous ARP/NDP requests, and confirms bidirectional communication
to a test service.

DynIP draws a distinction between a configured IP and a used IP for purposes of determining if a node
needs an additional allocation

## Location
A location is a logical tag used to identify which groups can be used by which nodes

## Grouping
A grouping defines a single IP space which is subdivided into allocations a node can reserve.

## Active Utilization
An actively utilized allocation is one that is both configured on a system, and in use by some service
or server. An allocation is actively utilized if any IP addresses that compromise it are being utilized
Utilization can be automatically determined by socket usage, or by a third-party tracking state.

When any IP in an allocation is utilized, it locks the allocation block its in to that node and will
not be released. In case of restart or interface reset, actively utilized allocations are automatically
configured when dynipd starts.

## Standby
To make sure that additional IPs are available for services on demand, DynIPD allows a network administrator
to set a number of IPs that are available but unused. These IPs are configured on an interface, and as part
of the configuration process, known to be functional and active. When using allocations larger than an
individual IP to a specific machine, all those IPs within that allocation are marked standby until they
move to active utilization status.

If an entire allocation is in standby status, it becomes a candidate to be released. IPs are released
to the pool based on policy settings.

## Reserved IPs
A reserved IP is one a machine claimed, but has not configured, or confirmed active. IPs remain in
a reserve state until the test service confirms that its active. The reserved step allows for networks
that depend on cache timeouts to still use this service. A machine must renew its reservation to avoid
deadlocks; after a timeout, a reserved IP automatically returns to the available pool

## Available Allocations
Anything left remains in a pool for any node to claim as needed.

## Unmanaged Allocation
Blocks can also be marked as unmanaged. This is to allow a network administrator to manually
configure these blocks as they see fit; i.e., to assign all machines a single stack IP for initial
startup and configuration. Unmanaged blocks can be assigned to a machine for tracking purposes, but
will not be used unless their status is moved to unallocated by hand.

# Life Cycle of an Allocation
To prevent unexpected configuration changes, allocations can only move from one state to an immediately
adjacent state. To summarize, the list of states are:

+ Actively Utilized
+ Standby
+ Reserved
+ Unallocated
+ Unmanaged

When dynipd is first setup, all allocations within a group are marked as unallocated. As clients start,
they determine how many IPs they need based on policy settings. These allocations move to reserved status
as a machine configures their network interfaces with the blocks in question. To move from reserved to standby
bidirectional communication must be tested and confirmed operational.

Once in standby status, IPs move to utilized status based on if an application has opened a socket on that IP,
or if its been marked by some 3rd party source. If and when an IP becomes available, it moves to standby status.
If a machine ends up with too many standby allocations as defined by policy, the block moves to reserve status,
and then times out to go back to unallocated. This allows for a machine to rapidly reclaim IPs if necessary.

Once the reservation times out, the block becomes unallocated, and can be freely claimed by any client in need
of its resources.
