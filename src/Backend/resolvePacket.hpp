// resolve all kind of packet

#include <spdlog/spdlog.h>

#include <uvw.hpp>

#ifdef __cplusplus
extern "C" {
#endif

#include <icmp_proto.h>
#include <stdint.h>
#include <stdio.h>

#ifdef __cplusplus
}
#endif

int resolve_network_packet(void *in_pck, uint32_t in_size, void *out_pck, uint32_t *out_size, uint8_t ip_addr[4]) {
    return resolve_packet(in_pck, in_size, out_pck, out_size, ip_addr);
}

int resolve_frontend_packet(const uvw::DataEvent &evt, char **out_pck, uint32_t &out_size) {
    const int maxlen = evt.length;  // must <= 64*1024
    *out_pck = new char [maxlen];
    for (int i = 0; i < maxlen; ++i) (*out_pck)[i] = evt.data[i];
    out_size = maxlen;
    return 0;
}
