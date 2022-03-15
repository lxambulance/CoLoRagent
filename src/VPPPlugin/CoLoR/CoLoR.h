
/*
 * CoLoR.h - skeleton vpp engine plug-in header file
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
#ifndef __included_CoLoR_h__
#define __included_CoLoR_h__

#include <vnet/vnet.h>
#include <vnet/ip/ip.h>
#include <vnet/ethernet/ethernet.h>

#include <vppinfra/hash.h>
#include <vppinfra/error.h>

typedef struct
{
  /* API message ID base */
  u16 msg_id_base;

  /* on/off switch for the periodic function */
  u8 periodic_timer_enabled;
  /* Node index, non-zero if the periodic process has been created */
  u32 periodic_node_index;

  /* convenience */
  vlib_main_t *vlib_main;
  vnet_main_t *vnet_main;
  ethernet_main_t *ethernet_main;
} CoLoR_main_t;

#define foreach_CoLoR_error _ (SWAPPED, "Mac swap packets processed")

typedef enum
{
#define _(sym, str) COLOR_ERROR_##sym,
  foreach_CoLoR_error
#undef _
    COLOR_N_ERROR,
} CoLoR_error_t;

#ifndef CLIB_MARCH_VARIANT
static char *CoLoR_error_strings[] = {
#define _(sym, string) string,
  foreach_CoLoR_error
#undef _
};
#endif /* CLIB_MARCH_VARIANT */

/* CoLoR protocol packet format, header part 1 */
typedef union
{
  struct
  {
    u8 CoLoR_version_and_packet_type;
#define COLOR_VERSION_MASK   (15 << 4)
#define PACKET_TYPE_MASK     (15)
#define get_color_version(x) (((x) &COLOR_VERSION_MASK) >> 4)
#define get_packet_type(x)   (((x) &PACKET_TYPE_MASK) - 1)
    u8 ttl;
    u16 packet_length;
    u16 checksum;
  };
  CLIB_PACKED (struct { u16 checksum_data[3]; });
} CoLoR_header_t;

static char *CoLoR_packet_type_strings[] = { "ANN", "GET", "DATA", "CONTROL" };

u8 *format_CoLoR_header (u8 *s, va_list *args);

extern CoLoR_main_t CoLoR_main;

extern vlib_node_registration_t CoLoR_lookup_node;
extern vlib_node_registration_t CoLoR_input_node;
extern vlib_node_registration_t CoLoR_output_node;
extern vlib_node_registration_t CoLoR_periodic_node;

/* Periodic function events */
#define COLOR_EVENT1			    1
#define COLOR_EVENT2			    2
#define COLOR_EVENT_PERIODIC_ENABLE_DISABLE 3

void CoLoR_create_periodic_process (CoLoR_main_t *);

#endif /* __included_CoLoR_h__ */

/*
 * fd.io coding-style-patch-verification: ON
 *
 * Local Variables:
 * eval: (c-set-style "gnu")
 * End:
 */
