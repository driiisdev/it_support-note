# Practice: Subnet Planner (The Network Layer)

Concept note:
[`the-network-layer.md`](<../../../concepts/computer networking/the-network-layer.md>)

## What this demonstrates

Subnetting as **bit operations you can see**: the network ID is `IP AND mask`, the broadcast is
`network OR wildcard`, usable hosts are `2^hostbits − 2`. Then it applies that to a real planning
task: carving an office's address block into right-sized subnets per department (**VLSM**), the
table that becomes your VLANs and DHCP scopes.

## Scenario

Your company is opening a new office and has been given `10.20.0.0/22`. You need subnets for
staff, guest Wi-Fi, VoIP phones, servers, printers, network management, and a point-to-point link
to the firewall - each with room to grow - and you need to explain your plan to the network admin.

## Folder structure

```
subnet-planner/
  subnet_calc.py            <- one subnet in detail (binary AND shown), same-subnet check, quiz mode
  vlsm_planner.py           <- allocate a block across departments, biggest first
  office-requirements.csv   <- department, VLAN ID, number of hosts
```

## Code walkthrough

**The whole of subnetting is three bitwise operations:**

```python
mask      = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF   # /26 -> 255.255.255.192
network   = ip & mask                                    # AND zeroes the host bits
broadcast = network | (~mask & 0xFFFFFFFF)               # OR sets all host bits to 1
```

`subnet_calc.py` prints those operations in binary so you can see the boundary, then
**cross-checks** against Python's `ipaddress` module - if the hand math were wrong, the
`assert` would fail.

**`same`** answers the core routing question every host asks: *is the destination on my subnet
(send directly), or not (send to the gateway)?*

**VLSM: biggest first.** A `/24` must start on a multiple of 256, a `/27` on a multiple of 32.
Allocating the largest subnets first keeps every subnet aligned with no wasted gaps:

```python
r["prefix"] = prefix_for(hosts_with_growth)   # smallest subnet where 2^h - 2 >= hosts
reqs.sort(key=lambda r: r["prefix"])          # small prefix number = big subnet = first
```

## Run it

```bash
python subnet_calc.py 192.168.10.70/26
python subnet_calc.py 10.1.5.200 255.255.240.0
python subnet_calc.py same 192.168.1.10 192.168.1.200 25
python subnet_calc.py quiz

python vlsm_planner.py                      # 10.20.0.0/22 + office-requirements.csv, 20% growth
python vlsm_planner.py --growth 50
python vlsm_planner.py 10.20.0.0/24         # see what happens when the block is too small
```

Expected (`vlsm_planner.py`, excerpt):

```
NAME           VLAN  HOSTS  NEED  SUBNET            MASK             GATEWAY        RANGE
Staff            10    180   216  10.20.0.0/24      255.255.255.0    10.20.0.1      10.20.0.2 - 10.20.0.254
Guest-WiFi       20    100   120  10.20.1.0/25      255.255.255.128  10.20.1.1      10.20.1.2 - 10.20.1.126
VoIP-Phones      30     60    72  10.20.1.128/25    255.255.255.128  10.20.1.129    ...
...
Unallocated: 424 addresses starting at 10.20.2.88
```

> Note for Git Bash users: write prefixes as `25`, not `/25`, in the `same` command - Git Bash
> rewrites arguments starting with `/` into Windows paths. PowerShell and cmd don't.

## Try this yourself

- Do 10 questions with `python subnet_calc.py quiz` **on paper first**. Aim for under 30 seconds each
  using the block-size shortcut (256 − mask octet).
- Run `ipconfig` and feed your own IP + mask into `subnet_calc.py`. How many devices could your home
  network hold?
- Add a department with 500 hosts to the CSV. What's the smallest block that fits everything now?
- Add a `--summarize` option that prints the single route (supernet) covering all allocated subnets
  (hint: `ipaddress.collapse_addresses`).
- Turn the VLSM output into DHCP scope definitions: for each subnet, scope = range after the first
  10 addresses (reserved for static devices), gateway option = first address.

## Real-world equivalent

- **IP address management (IPAM)** tools - NetBox, phpIPAM, Infoblox, Windows Server IPAM - track
  exactly this table.
- Every new site, VLAN, VPN, or cloud VPC (AWS/Azure require you to pick CIDR blocks for subnets)
  starts with this exercise. Overlapping ranges between sites is a classic mistake that breaks
  VPNs later - plan once, document it.
