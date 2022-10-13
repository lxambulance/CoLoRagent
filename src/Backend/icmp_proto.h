/*
 *------------------------------------------------------------------
 * Copyright (c) 2017 Cisco and/or its affiliates.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at:
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *------------------------------------------------------------------
 */

#ifndef _ICMP_PROTO_H_
#define _ICMP_PROTO_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <arpa/inet.h>
#include <asm/byteorder.h>
#include <assert.h>
#include <byteswap.h>
#include <fcntl.h>
#include <inttypes.h>
#include <linux/icmp.h>
#include <linux/ip.h>
#include <net/if.h>
#include <net/if_arp.h>
#include <netdb.h>
#include <netinet/if_ether.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <sys/un.h>

typedef enum {
    ICMPR_FLOW_MODE_ETH = 0,
    ICMPR_FLOW_MODE_IP,
} icmpr_flow_mode_t;

uint16_t cksum(void *addr, ssize_t len);

int resolve_packet(void *in_pck, ssize_t in_size, void *out_pck, uint32_t *out_size, uint8_t ip_addr[4]);

/* resolve packet in place */
int resolve_packet2(void *pck, uint32_t *size, uint8_t ip_addr[4]);

/* resolve packet in place and add eth encap */
int resolve_packet3(void **pck, uint32_t *size, uint8_t ip_addr[4]);

int generate_packet(void *pck, uint32_t *size, uint8_t saddr[4],
                    uint8_t daddr[4], uint8_t hw_daddr[6], uint32_t seq);

int generate_packet2(void *pck, uint32_t *size, uint8_t saddr[4],
                     uint8_t daddr[4], uint8_t hw_daddr[6], uint32_t seq,
                     icmpr_flow_mode_t);

int print_packet(void *pck);

ssize_t resolve_arp(void *arp);

ssize_t resolve_eth_arp(struct ether_arp *eth_arp, void *eth_arp_resp, uint8_t ip_addr[4]);

ssize_t resolve_eth(struct ether_header *eth, void *eth_resp);

ssize_t resolve_ip(struct iphdr *ip, void *ip_resp, uint8_t ip_addr[4]);

ssize_t resolve_icmp(struct icmphdr *icmp, void *icmp_resp);

ssize_t generate_eth(struct ether_header *eh, uint8_t hw_daddr[6]);

ssize_t generate_ip(struct iphdr *ip, uint8_t saddr[4], uint8_t daddr[4]);

ssize_t generate_icmp(struct icmphdr *icmp, uint32_t seq);

#ifdef __cplusplus
}
#endif

#endif /* _ICMP_PROTO_H_ */
