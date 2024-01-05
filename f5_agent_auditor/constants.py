# -*- coding: utf-8 -*-

# we donot check selfip, route_domain, vlan, because these resources
# are audited by Neutron DB.

EXCLUSIVE_RESOURCES = [
    "selfip", "pool", "persistence", "member", "route_domain",
    "vlan", "folder",

    "sys", "device", "hash_persistence", "websocket_profile",
    "tunnel", "arp", "msrdp_persistence",
    "ssl_persistence", "oneconnect"
]

# checking diff of shared network resource
# selfip (tenant id, subnet id), is always different because of the hostname.
# vlan (tenant id, network segement),
# route_domain (tenant id, network segement),
# gw (tenant id, gateway ip, network segement)
SHARED_NET_RESOURCES = [
    "vlan", "route_domain", "route"
]

# checking diff of loadbalancer (lb id)
LOADBALANCER_RESOURCES = [
    "virtual_address", "snatpool",
]

# checking diff of listener (ls id?)
LISTENER_RESOURCES = [
    "cookie_persistence", "universal_persistence",
    "sip_persistence", "source_addr_persistence",

    "http_profile", "tcp_profile", "http2_profile",

    "server_ssl_profile", "ssl_cert_file", "client_ssl_profile",
    "cipher_group", "cipher_rule",

    "bwc_policy", "l7policy"
]

# checking diff of monitor (monitor id)
MONITOR_RESOURCES = [
    "http_monitor", "https_monitor", "tcp_monitor", "ping_monitor"
]

SPEC_RESOURCES = [
    "selfip", "pool", "member"
]

EXCLUSIVE_KEYS = [
    "ifIndex", "generation", "creationTime",
    "lastModifiedTime", "vsIndex", "ifIndex",
    "selfDevice", "expirationString", "lastUpdateTime",
    "checksum", "serialNumber", "expirationDate",
    "fingerprint", "createTime", "vlansReference",
    "revision", "passphrase", "subject", "lastModified",
    "members_s", "membersReference"
]
