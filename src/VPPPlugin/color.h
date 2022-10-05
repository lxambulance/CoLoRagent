
/*
 * color.h - color protocol header file
 *
 * Copyright (c) <current-year> <your-organization>
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
 */
#ifndef __included_color_h__
#define __included_color_h__

#include <vnet/vnet.h>
#include <vnet/ip/ip.h>
#include <vnet/ethernet/ethernet.h>

#include <vppinfra/hash.h>
#include <vppinfra/error.h>
#include <vppinfra/fifo.h>

typedef struct
{
  /* stream control status */
  u32 flags;
  /* stream is enabled now */
#define COLOR_STREAM_FLAGS_IS_ENABLED (1<<0)

  /* file prepare to send */
  u8* file_name;

  /* arguments for send rate*/
  u32 max_packet_bytes;
  u64 n_packets_generated;
  f64 rate_packets_per_second;
  f64 time_last_generate;
  f64 packet_accumulator;

  /* worker thread index */
  u32 worker_index;
}color_stream_t;

typedef struct
{
  /* Pool of streams. */
  color_stream_t *streams;

  /* Bitmap indicating which streams are currently enabled. */
  uword **enabled_streams;

  /* API message ID base */
  u16 msg_id_base;

  /* on/off switch for the periodic function */
  u8 periodic_timer_enabled;
  /* Node index, non-zero if the periodic process has been created */
  u32 periodic_node_index;

  u32 *tx_buffers;
  /* receive buffer pointer fifo queue, max size is RX_LIMIT(see below) */
  vlib_buffer_t **rx_fifo_queue;

  /* convenience */
  // TODO: remove this three elements
  vlib_main_t *vlib_main;
  vnet_main_t *vnet_main;
  ethernet_main_t *ethernet_main;
} color_main_t;

#define foreach_color_error                                                   \
  _ (NONE, "valid color packets")                                             \
  /* Errors signalled by color-lookup */                                      \
  _ (BAD_CHECKSUM, "bad color checksum")                                      \
  _ (BAD_LENGTH, "color length != ip4 length - 20")                           \
  _ (TIME_EXPIRED, "color ttl < 1")                                           \
  /* Errors signalled by color-input */                                       \
  _ (NO_RESPONSE, "no response to announce packet")

typedef enum
{
#define _(sym, str) COLOR_ERROR_##sym,
  foreach_color_error
#undef _
    COLOR_N_ERROR,
} color_error_t;

#ifndef CLIB_MARCH_VARIANT
static char *color_error_strings[] = {
#define _(sym, string) string,
  foreach_color_error
#undef _
};
#endif /* CLIB_MARCH_VARIANT */

/* color protocol packet format, header part 1 */
typedef union
{
  struct
  {
    u8 color_version_and_packet_type;
#define COLOR_VERSION_MASK   (15 << 4)
#define PACKET_TYPE_MASK     (15)
#define get_color_version(x) (((x) &COLOR_VERSION_MASK) >> 4)
#define get_packet_type(x)   (((x) &PACKET_TYPE_MASK) - 1)
    u8 ttl;
    u16 packet_length;
    u16 checksum;
  };
  CLIB_PACKED (struct { u16 checksum_data[3]; });
} color_header_t;

static char *color_packet_type_strings[] = { "ANN", "GET", "DATA", "CONTROL" };

u8 *format_color_header (u8 *s, va_list *args);

extern color_main_t color_main;

#define RX_LIMIT 1024
always_inline void
color_rx_push_back (vlib_buffer_t * bp)
{
  if (clib_fifo_elts (color_main.rx_fifo_queue) < RX_LIMIT)
    clib_fifo_add1 (color_main.rx_fifo_queue, bp);
}
always_inline vlib_buffer_t *
color_rx_pop_front ()
{
  vlib_buffer_t *ret = NULL;
  if (clib_fifo_elts (color_main.rx_fifo_queue) > 0)
    clib_fifo_sub1 (color_main.rx_fifo_queue, ret);
  return ret;
}

extern vlib_node_registration_t color_lookup_node;
extern vlib_node_registration_t color_input_node;
extern vlib_node_registration_t color_output_node;
extern vlib_node_registration_t color_periodic_node;

/* Periodic function events */
#define COLOR_EVENT1			    1
#define COLOR_EVENT2			    2
#define COLOR_EVENT_PERIODIC_ENABLE_DISABLE 3

void color_create_periodic_process (color_main_t *);

#endif /* __included_color_h__ */

/*
 * fd.io coding-style-patch-verification: ON
 *
 * Local Variables:
 * eval: (c-set-style "gnu")
 * End:
 */
