// resolve all kind of packet

#include <icmp_proto.h>
#include <spdlog/spdlog.h>
#include <stdint.h>

#include <uvw.hpp>

int resolve_network_packet(char *in_pck, uint32_t in_size, char *out_pck, uint32_t *out_size, uint8_t ip_addr[4]) {
    struct ether_arp *eah;
    struct iphdr *ip, *ip_out;
    struct icmphdr *icmp;
    *out_size = 0;

    if ((in_pck == NULL) || (out_pck == NULL))
        return -1;

    struct ether_header *eh = (struct ether_header *)in_pck;
    *out_size = resolve_eth(eh, out_pck);

    if (eh->ether_type == 0x0608) {
        eah = (struct ether_arp *)(in_pck + *out_size);
        *out_size += resolve_eth_arp(eah, out_pck + *out_size, ip_addr);
    } else if (eh->ether_type == 0x0008) {
        ip = (struct iphdr *)(in_pck + *out_size);
        ip_out = (struct iphdr *)(out_pck + *out_size);
        *out_size += resolve_ip(ip, out_pck + *out_size, ip_addr);
        if (ip->protocol == 1) {
            icmp = (struct icmphdr *)(in_pck + *out_size);
            *out_size += resolve_icmp(icmp, out_pck + *out_size);
            ((struct icmphdr *)(out_pck + *out_size - sizeof(struct icmphdr)))->checksum = cksum(out_pck + *out_size - sizeof(struct icmphdr), sizeof(struct icmphdr));
            /* payload */
            memcpy(out_pck + *out_size, in_pck + *out_size, in_size - *out_size);
            *out_size = in_size;
            ip_out->tot_len = htons(*out_size - sizeof(struct ether_header));
            ip_out->check = cksum(ip_out, sizeof(struct iphdr));
        } else if (ip->protocol == 150) {
            spdlog::debug("Oh!!! we got color packet.");
        }
    }
    return 0;
}

int resolve_frontend_packet(const uvw::DataEvent &evt, char **out_pck, uint32_t &out_size) {
    const int maxlen = evt.length;  // must <= 64*1024
    *out_pck = new char[maxlen];
    for (int i = 0; i < maxlen; ++i) (*out_pck)[i] = evt.data[i];
    out_size = maxlen;
    return 0;
}
