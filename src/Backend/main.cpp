// color backend main

#include <spdlog/spdlog.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <uvw.hpp>

#ifdef __cplusplus
extern "C" {
#endif

#include <error.h>
#include <icmp_proto.h>
#include <libmemif.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#ifdef __cplusplus
}
#endif

char APP_NAME[16] = "colorBackend";
#define IF_NAME "colorMemif"
#define SOCKET_NAME "/run/vpp/memif.sock"
#define ICMPR_HEADROOM 64
#define MAX_MEMIF_BUFS 256

struct memif_connection_t {
    uint16_t index;
    /* memif connection handle */
    memif_conn_handle_t conn;
    /* tx buffers */
    memif_buffer_t *tx_bufs;
    /* allocated tx buffers counter */
    /* number of tx buffers pointing to shared memory */
    uint16_t tx_buf_num;
    /* rx buffers */
    memif_buffer_t *rx_bufs;
    /* allocated rx buffers counter */
    /* number of rx buffers pointing to shared memory */
    uint16_t rx_buf_num;
    /* interface ip address */
    uint8_t ip_addr[4];
    uint16_t seq;
    uint64_t tx_counter, rx_counter, tx_err_counter;
    uint64_t t_sec, t_nsec;
};

struct icmpr_thread_data_t {
    uint16_t index;
    uint64_t packet_num;
    uint8_t ip_daddr[4];
    uint8_t hw_daddr[6];
};

memif_connection_t memif_connection;
icmpr_thread_data_t icmpr_thread_data;
struct sockaddr_un saddr;
int connection_socket;
memif_conn_args_t args;

static void printHelp() {
    spdlog::info("APP NAME: {:s} - MODIFY FROM LIBMEMIF EXAMPLE APP", APP_NAME);
    spdlog::info("{:=<30}", "");
    spdlog::info("memif version: {:04x}", memif_get_version());
    spdlog::info("valid commands:");
    spdlog::info("\tquit|q - exit app");
    spdlog::info("\thelp - prints this help");
    spdlog::info("\tshow - show connection details");
    spdlog::info("\tsh-count - print counters");
    spdlog::info("\tcl-count - clear counters");
    // spdlog::info("\tsend - send icmp/ping reply");
}

static void printDetails() {
    spdlog::info("MEMIF DETAILS");
    spdlog::info("{:=<30}", "");
    memif_details_t md;
    ssize_t buflen = 2048;
    char *buf = (char *)malloc(buflen);
    memif_connection_t *c = &memif_connection;
    memset(&md, 0, sizeof(md));
    memset(buf, 0, buflen);
    int err = memif_get_details(c->conn, &md, buf, buflen);
    if (err != MEMIF_ERR_SUCCESS) {
        if (err != MEMIF_ERR_NOCONN)
            spdlog::error("%s", memif_strerror(err));
        return;
    }
    spdlog::info("interface index: {:d}", c->index);
    spdlog::info("\tinterface ip: {:d}.{:d}.{:d}.{:d}", c->ip_addr[0], c->ip_addr[1], c->ip_addr[2], c->ip_addr[3]);
    spdlog::info("\tinterface name: {:s}", (char *)md.if_name);
    spdlog::info("\tapp name: {:s}", (char *)md.inst_name);
    spdlog::info("\tremote interface name: {:s}", (char *)md.remote_if_name);
    spdlog::info("\tremote app name: {:s}", (char *)md.remote_inst_name);
    spdlog::info("\tid: {:d}", md.id);
    std::ostringstream s;
    s.str(""), s.clear();
    s << "\tsecret: " << (char *)md.secret;
    spdlog::info(s.str());
    s.str(""), s.clear();
    s << "\trole: ";
    if (md.role)
        s << "slave";
    else
        s << "master";
    spdlog::info(s.str());
    s.str(""), s.clear();
    s << "\tmode: ";
    switch (md.mode) {
        case 0:
            s << "ethernet";
            break;
        case 1:
            s << "ip";
            break;
        case 2:
            s << "punt/inject";
            break;
        default:
            s << "unknown";
            break;
    }
    spdlog::info(s.str());
    spdlog::info("\tsocket filename: {:s}", (char *)md.socket_filename);
    spdlog::info("\trx queues:");
    for (int e = 0; e < md.rx_queues_num; e++) {
        spdlog::info("\t\tqueue id: {:d}", md.rx_queues[e].qid);
        spdlog::info("\t\tring size: {:d}", md.rx_queues[e].ring_size);
        spdlog::info("\t\tring rx mode: {:s}", md.rx_queues[e].flags ? "polling" : "interrupt");
        spdlog::info("\t\tring head: {:d}", md.rx_queues[e].head);
        spdlog::info("\t\tring tail: {:d}", md.rx_queues[e].tail);
        spdlog::info("\t\tbuffer size: {:d}", md.rx_queues[e].buffer_size);
    }
    spdlog::info("\ttx queues:");
    for (int e = 0; e < md.tx_queues_num; e++) {
        spdlog::info("\t\tqueue id: {:d}", md.tx_queues[e].qid);
        spdlog::info("\t\tring size: {:d}", md.tx_queues[e].ring_size);
        spdlog::info("\t\tring rx mode: {:s}", md.tx_queues[e].flags ? "polling" : "interrupt");
        spdlog::info("\t\tring head: {:d}", md.tx_queues[e].head);
        spdlog::info("\t\tring tail: {:d}", md.tx_queues[e].tail);
        spdlog::info("\t\tbuffer size: {:d}", md.tx_queues[e].buffer_size);
    }
    s.str(""), s.clear();
    s << "\tlink: ";
    if (md.link_up_down)
        s << "up";
    else {
        s << "down";
        spdlog::info(s.str());
        s.str(""), s.clear();
        s << "\treason: " << md.error;
    }
    spdlog::info(s.str());
    free(buf);
}

void printCounters() {
    spdlog::info("show counters");
    memif_connection_t *c = &memif_connection;
    if (c->conn == NULL) return;
    spdlog::info("{:=<30}", "");
    spdlog::info("interface index: {:d}", c->index);
    spdlog::info("\trx: {:d}", c->rx_counter);
    spdlog::info("\ttx: {:d}", c->tx_counter);
    spdlog::info("\ttx_err: {:d}", c->tx_err_counter);
    spdlog::info("\tts: {:d}s {:d}ns", c->t_sec, c->t_nsec);
}

void clearCounters() {
    spdlog::debug("clear counters");
    memif_connection_t *c = &memif_connection;
    if (c->conn == NULL) return;
    c->t_sec = c->t_nsec = c->tx_err_counter = c->tx_counter = c->rx_counter = 0;
}

void sendICMPRep() {
    spdlog::debug("send icmp ping reply");
}

void deleteMemif() {
    spdlog::debug("delete memif");
    auto loop = uvw::Loop::getDefault();
    loop->walk(uvw::Overloaded{
        [](uvw::PollHandle &poll) { poll.close(); },
        [](auto &&) { /* ignore all other types */ }});
    memif_connection_t *c = &memif_connection;
    if (c->rx_bufs) free(c->rx_bufs);
    if (c->tx_bufs) free(c->tx_bufs);
    c->rx_bufs = c->tx_bufs = NULL;
    c->rx_buf_num = c->tx_buf_num = 0;
    int err = memif_delete(&c->conn);
    if (err != MEMIF_ERR_SUCCESS) spdlog::error("memif_delete: %s", memif_strerror(err));
    if (c->conn != NULL) spdlog::error("memif delete fail");
    err = memif_cleanup();
    if (err != MEMIF_ERR_SUCCESS) spdlog::error("memif_cleanup: %s", memif_strerror(err));
}

void addUserInput() {
    auto loop = uvw::Loop::getDefault();
    // 注册终端读事件到主循环
    auto tty = loop->resource<uvw::TTYHandle>(uvw::StdIN, true);
    tty->on<uvw::DataEvent>([](uvw::DataEvent &evt, uvw::TTYHandle &tty) {
        if (evt.length == 1 && evt.data[0] == '\n') return;
        evt.data[evt.length - 1] = 0;
        spdlog::debug("user input size={:d} data=\"{:s}\"", evt.length - 1, evt.data.get());
        char *ui = evt.data.get(), *end = nullptr;
        if (strncmp(ui, "quit", 4) == 0 || evt.length == 2 && strncmp(ui, "q", 1) == 0) {
            deleteMemif();
            tty.close();
        } else if (strncmp(ui, "help", 4) == 0) {
            printHelp();
        } else if (strncmp(ui, "show", 4) == 0) {
            printDetails();
        } else if (strncmp(ui, "sh-count", 8) == 0) {
            printCounters();
        } else if (strncmp(ui, "cl-count", 8) == 0) {
            clearCounters();
        } else if (strncmp(ui, "send", 4) == 0) {
            sendICMPRep();
        } else {
            spdlog::info("unknown command: {:s}", evt.data.get());
        }
    });
    tty->read();
}

int add_uv_fd(int fd, uint32_t events) {
    if (fd < 0) {
        spdlog::error("invalid fd {:d}", fd);
        return -1;
    }
    spdlog::debug("add fd={:d} evt={:d}", fd, events);
    auto loop = uvw::Loop::getDefault();
    auto poll = loop->resource<uvw::PollHandle>(fd);
    poll->data(std::make_shared<int>(fd));  // 自定义方式保存fd，上面那个取不出来。
    poll->on<uvw::PollEvent>([nowfd = fd](uvw::PollEvent &evt, uvw::PollHandle &poll) {
        uint32_t events = 0;
        if (evt.flags & uvw::PollHandle::Event::READABLE) events |= MEMIF_FD_EVENT_READ;
        if (evt.flags & uvw::PollHandle::Event::WRITABLE) events |= MEMIF_FD_EVENT_WRITE;
        int memif_err = memif_control_fd_handler(nowfd, events);
        if (memif_err != MEMIF_ERR_SUCCESS)
            spdlog::error("memif_control_fd_handler: {:s} fd = {:d}", memif_strerror(memif_err), nowfd);
    });
    poll->on<uvw::ErrorEvent>([nowfd = fd](uvw::ErrorEvent &evt, uvw::PollHandle &poll) {
        uint32_t events = MEMIF_FD_EVENT_ERROR;
        int memif_err = memif_control_fd_handler(nowfd, events);
        if (memif_err != MEMIF_ERR_SUCCESS)
            spdlog::error("memif_control_fd_handler: {:s} fd = {:d}", memif_strerror(memif_err), nowfd);
    });
    uvw::Flags<uvw::PollHandle::Event> flags;
    if (events & UV_READABLE) flags = flags | uvw::PollHandle::Event::READABLE;
    if (events & UV_WRITABLE) flags = flags | uvw::PollHandle::Event::WRITABLE;
    poll->start(flags);
    // poll->start(uvw::Flags<uvw::PollHandle::Event>::from<uvw::PollHandle::Event::READABLE,uvw::PollHandle::Event::WRITABLE>());
    return 0;
}

int del_uv_fd(int fd) {
    spdlog::debug("del fd={:d}", fd);
    auto loop = uvw::Loop::getDefault();
    loop->walk(uvw::Overloaded{
        [nowfd = fd](uvw::PollHandle &poll) {
            std::shared_ptr<int> pdata = poll.data<int>();
            if (*pdata == nowfd) poll.close();
        },
        [](auto &&) { /* ignore all other types */ }});
    return 0;
}

int mod_uv_fd(int fd, uint32_t events) {
    spdlog::debug("mod fd={:d} evt={:d}", fd, events);
    auto loop = uvw::Loop::getDefault();
    loop->walk(uvw::Overloaded{
        [nowfd = fd, evts = events](uvw::PollHandle &poll) {
            std::shared_ptr<int> pdata = poll.data<int>();
            if (*pdata == nowfd) {
                poll.stop();
                uvw::Flags<uvw::PollHandle::Event> flags;
                if (evts & UV_READABLE) flags = flags | uvw::PollHandle::Event::READABLE;
                if (evts & UV_WRITABLE) flags = flags | uvw::PollHandle::Event::WRITABLE;
                poll.start(flags);
            }
        },
        [](auto &&) { /* ignore all other types */ }});

    return 0;
}

/* user needs to watch new fd or stop watching fd that is about to be closed.
    control fd will be modified during connection establishment to minimize CPU usage */
int control_fd_update(int fd, uint8_t events, void *ctx) {
    spdlog::debug("control_fd_update fd={:d} evt={:d}", fd, events);
    if (events & MEMIF_FD_EVENT_DEL) return del_uv_fd(fd);
    uint32_t evt = 0;
    if (events & MEMIF_FD_EVENT_READ) evt |= UV_READABLE;
    if (events & MEMIF_FD_EVENT_WRITE) evt |= UV_WRITABLE;
    if (events & MEMIF_FD_EVENT_MOD) return mod_uv_fd(fd, evt);
    return add_uv_fd(fd, evt);
}

/* called when event is polled on interrupt file descriptor.
    there are packets in shared memory ready to be received */
int on_interrupt(memif_conn_handle_t conn, void *private_ctx, uint16_t qid) {
    spdlog::debug("on_interrupt");
    memif_connection_t *c = &memif_connection;

    int err = MEMIF_ERR_SUCCESS, ret_val;
    uint16_t rx = 0, tx = 0;
    int i = 0; /* rx buffer iterator */
    int j = 0; /* tx buffer iterator */

    /* loop while there are packets in shm */
    do {
        /* receive data from shared memory buffers */
        err = memif_rx_burst(c->conn, qid, c->rx_bufs, MAX_MEMIF_BUFS, &rx);
        ret_val = err;
        c->rx_counter += rx;
        if ((err != MEMIF_ERR_SUCCESS) && (err != MEMIF_ERR_NOBUF)) {
            spdlog::error("memif_rx_burst: {:}", memif_strerror(err));
            goto error;
        }

        i = 0;
        memset(c->tx_bufs, 0, sizeof(memif_buffer_t) * rx);
        err = memif_buffer_alloc(c->conn, qid, c->tx_bufs, rx, &tx, 128);
        if ((err != MEMIF_ERR_SUCCESS) && (err != MEMIF_ERR_NOBUF_RING)) {
            spdlog::error("memif_buffer_alloc: {:}", memif_strerror(err));
            goto error;
        }
        j = 0;
        c->tx_err_counter += rx - tx;

        while (tx) {
            spdlog::debug("receive packet len = {:d}, data = ", (c->rx_bufs + i)->len);
            std::ostringstream s;
            int clen = (c->rx_bufs + i)->len;
            unsigned char * ch = static_cast<unsigned char *>((c->rx_bufs + i)->data);
            for (int k = 0; k < clen; ++k)
                s << std::setfill('0') << std::setw(2) << std::hex << (unsigned int)*(ch + k);
            spdlog::debug(s.str());
            resolve_packet((void *)(c->rx_bufs + i)->data,
                           (c->rx_bufs + i)->len,
                           (void *)(c->tx_bufs + j)->data,
                           &(c->tx_bufs + j)->len, c->ip_addr);
            i++;
            j++;
            tx--;
        }

        err = memif_refill_queue(c->conn, qid, rx, ICMPR_HEADROOM);
        if (err != MEMIF_ERR_SUCCESS)
            spdlog::error("memif_buffer_free: {:}", memif_strerror(err));
        rx -= rx;

        spdlog::debug("{:d}/{:d} alloc/free buffers", rx, MAX_MEMIF_BUFS - rx);

        err = memif_tx_burst(c->conn, qid, c->tx_bufs, j, &tx);
        if (err != MEMIF_ERR_SUCCESS) {
            spdlog::error("memif_tx_burst: {:}", memif_strerror(err));
            goto error;
        }
        c->tx_counter += tx;

    } while (ret_val == MEMIF_ERR_NOBUF);

    return 0;

error:
    err = memif_refill_queue(c->conn, qid, rx, ICMPR_HEADROOM);
    if (err != MEMIF_ERR_SUCCESS)
        spdlog::error("memif_buffer_free: {:}", memif_strerror(err));
    c->rx_buf_num -= rx;
    spdlog::debug("freed {:d} buffers. {:d}/{:d} alloc/free buffers", rx, c->rx_buf_num, MAX_MEMIF_BUFS - c->rx_buf_num);
    return 0;
}

int on_connect(memif_conn_handle_t conn, void *private_ctx) {
    spdlog::debug("memif connected!");
    memif_refill_queue(conn, 0, -1, ICMPR_HEADROOM);
    printHelp();
    return 0;
}

int on_disconnect(memif_conn_handle_t conn, void *private_ctx) {
    spdlog::debug("memif disconnected!");
    return 0;
}

void connectColorProtocolStack() {
    // 初始化memif
    int err = memif_init(control_fd_update, APP_NAME, NULL, NULL, NULL);
    spdlog::debug("memif_init: {:s}", memif_strerror(err));
    if (err != MEMIF_ERR_SUCCESS) exit(EXIT_FAILURE);
    memset(&memif_connection, 0, sizeof(memif_connection_t));
    // 建立memif共享内存接口
    memif_connection_t *c = &memif_connection;
    memset(&args, 0, sizeof(args));
    args.is_master = 0;
    args.log2_ring_size = 11;
    args.buffer_size = 2048;
    args.num_s2m_rings = 1;
    args.num_m2s_rings = 1;
    strncpy((char *)args.interface_name, IF_NAME, strlen(IF_NAME));
    args.mode = MEMIF_INTERFACE_MODE_ETHERNET;
    args.interface_id = 0;
    err = memif_create(&c->conn, &args, on_connect, on_disconnect, on_interrupt, NULL);
    spdlog::debug("memif_create: {:s}", memif_strerror(err));
    if (err != MEMIF_ERR_SUCCESS) exit(EXIT_FAILURE);
    c->rx_buf_num = 0;
    c->rx_bufs = (memif_buffer_t *)malloc(sizeof(memif_buffer_t) * MAX_MEMIF_BUFS);
    c->tx_buf_num = 0;
    c->tx_bufs = (memif_buffer_t *)malloc(sizeof(memif_buffer_t) * MAX_MEMIF_BUFS);
    c->ip_addr[0] = 192;
    c->ip_addr[1] = 168;
    c->ip_addr[2] = 1;
    c->ip_addr[3] = 2;
    c->seq = c->tx_err_counter = c->tx_counter = c->rx_counter = 0;
}

int main() {
    spdlog::set_level(spdlog::level::debug);
    auto loop = uvw::Loop::getDefault();
    connectColorProtocolStack();
    addUserInput();
    loop->run();
    return 0;
}
