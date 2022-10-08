/*
 * node.c - skeleton vpp engine plug-in dual-loop node skeleton
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
#include <vlib/vlib.h>
#include <vnet/vnet.h>
#include <vnet/pg/pg.h>
#include <vppinfra/error.h>
#include <color/color.h>
#include <color/color_packet.h>

typedef struct
{
  u8 packet_data[160];
  u8 next;
} color_output_trace_t;

always_inline void
swap_ip4_address (u32 *a, u32 *b)
{
  u32 c = *a;
  (*a) = (*b);
  (*b) = c;
}

#ifndef CLIB_MARCH_VARIANT

/* packet trace format function */
static u8 *
format_color_output_trace (u8 *s, va_list *args)
{
  CLIB_UNUSED (vlib_main_t * vm) = va_arg (*args, vlib_main_t *);
  CLIB_UNUSED (vlib_node_t * node) = va_arg (*args, vlib_node_t *);
  color_output_trace_t *t = va_arg (*args, color_output_trace_t *);

  u32 indent = format_get_indent (s);
  s = format (s, "%U\n", format_color_packet, t->packet_data);
  s = format (s, "%Unext node:", format_white_space, indent);
  if (t->next == 0)
    s = format (s, "drop");
  else
    s = format (s, "ip4-lookup");

  return s;
}

vlib_node_registration_t color_output_node;

#endif /* CLIB_MARCH_VARIANT */

typedef enum
{
  COLOR_OUTPUT_NEXT_DROP,
  COLOR_OUTPUT_NEXT_IP4,
  COLOR_OUTPUT_N_NEXT,
} color_output_next_t;

always_inline uword
color_output_inline (vlib_main_t *vm, vlib_node_runtime_t *node,
		     vlib_frame_t *frame, int is_ip4, int is_trace)
{
  u32 n_left_from, *from;
  vlib_buffer_t *bufs[VLIB_FRAME_SIZE], **b;
  u16 nexts[VLIB_FRAME_SIZE], *next;

  from = vlib_frame_vector_args (frame);
  n_left_from = frame->n_vectors;

  if (node->flags & VLIB_NODE_FLAG_TRACE)
    vlib_trace_frame_buffers_only (vm, node, from, frame->n_vectors, 0,
				   sizeof (color_output_trace_t));

  vlib_get_buffers (vm, from, bufs, n_left_from);
  b = bufs;
  next = nexts;

  while (n_left_from >= 4)
    {
      ip4_header_t *ip[4];

      /* Prefetch next iteration. */
      if (PREDICT_TRUE (n_left_from >= 8))
	{
	  vlib_prefetch_buffer_header (b[4], STORE);
	  vlib_prefetch_buffer_header (b[5], STORE);
	  vlib_prefetch_buffer_header (b[6], STORE);
	  vlib_prefetch_buffer_header (b[7], STORE);
	  CLIB_PREFETCH (b[4]->data, CLIB_CACHE_LINE_BYTES, STORE);
	  CLIB_PREFETCH (b[5]->data, CLIB_CACHE_LINE_BYTES, STORE);
	  CLIB_PREFETCH (b[6]->data, CLIB_CACHE_LINE_BYTES, STORE);
	  CLIB_PREFETCH (b[7]->data, CLIB_CACHE_LINE_BYTES, STORE);
	}

      /* $$$$ process 4x pkts right here */
      next[0] = 0;
      next[1] = 0;
      next[2] = 0;
      next[3] = 0;

      vlib_buffer_advance (b[0], -20);
      vlib_buffer_advance (b[1], -20);
      vlib_buffer_advance (b[2], -20);
      vlib_buffer_advance (b[3], -20);
      ip[0] = vlib_buffer_get_current (b[0]);
      ip[1] = vlib_buffer_get_current (b[1]);
      ip[2] = vlib_buffer_get_current (b[2]);
      ip[3] = vlib_buffer_get_current (b[3]);
      swap_ip4_address (&ip[0]->src_address.data_u32,
			&ip[0]->dst_address.data_u32);
      swap_ip4_address (&ip[1]->src_address.data_u32,
			&ip[1]->dst_address.data_u32);
      swap_ip4_address (&ip[2]->src_address.data_u32,
			&ip[2]->dst_address.data_u32);
      swap_ip4_address (&ip[3]->src_address.data_u32,
			&ip[3]->dst_address.data_u32);

      b += 4;
      next += 4;
      n_left_from -= 4;
    }

  while (n_left_from > 0)
    {

      /* $$$$ process 1 pkt right here */
      next[0] = 0;
      ip4_header_t *ip0;
      vlib_buffer_advance (b[0], -20);
      ip0 = vlib_buffer_get_current (b[0]);
      swap_ip4_address (&ip0->src_address.data_u32,
			&ip0->dst_address.data_u32);

      b += 1;
      next += 1;
      n_left_from -= 1;
    }

  vlib_buffer_enqueue_to_next (vm, node, from, nexts, frame->n_vectors);

  return frame->n_vectors;
}

VLIB_NODE_FN (color_output_node)
(vlib_main_t *vm, vlib_node_runtime_t *node, vlib_frame_t *frame)
{
  uword i, n_packets = 0;
  color_main_t *cmp = &color_main;
  u32 worker_index = 0;
  if (vlib_num_workers ())
    worker_index = vlib_get_current_worker_index ();

  clib_bitmap_foreach (i, cmp->enabled_streams[worker_index])
    {
      // color_stream_t *s = vec_elt_at_index (cmp->streams, i);
      n_packets += 0;
    }
  
  return n_packets;
}

/* *INDENT-OFF* */
#ifndef CLIB_MARCH_VARIANT
VLIB_REGISTER_NODE (color_output_node) = 
{
  .flags = VLIB_NODE_FLAG_TRACE_SUPPORTED,
  .name = "color-output",
  .type = VLIB_NODE_TYPE_INPUT,
  .vector_size = sizeof (u32),

  .format_trace = format_color_output_trace,
  
  .state = VLIB_NODE_STATE_DISABLED,
  
  .n_errors = ARRAY_LEN(color_error_strings),
  .error_strings = color_error_strings,

  .n_next_nodes = COLOR_OUTPUT_N_NEXT,
  .next_nodes = {
        [COLOR_OUTPUT_NEXT_DROP] = "drop",
        [COLOR_OUTPUT_NEXT_IP4] = "ip4-lookup",
  },
};

#endif /* CLIB_MARCH_VARIANT */
/* *INDENT-ON* */
/*
 * fd.io coding-style-patch-verification: ON
 *
 * Local Variables:
 * eval: (c-set-style "gnu")
 * End:
 */
