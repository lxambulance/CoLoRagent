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
#include <CoLoR/CoLoR.h>

typedef struct
{
  u8 packet_data[128];
} CoLoR_input_trace_t;

#ifndef CLIB_MARCH_VARIANT

/* packet trace format function */
static u8 *
format_CoLoR_input_trace (u8 *s, va_list *args)
{
  CLIB_UNUSED (vlib_main_t * vm) = va_arg (*args, vlib_main_t *);
  CLIB_UNUSED (vlib_node_t * node) = va_arg (*args, vlib_node_t *);
  CoLoR_input_trace_t *t = va_arg (*args, CoLoR_input_trace_t *);

  s = format (s, "%U\n", format_CoLoR_header, t->packet_data,
	      sizeof (t->packet_data));
  return s;
}

vlib_node_registration_t CoLoR_input_node;

#endif /* CLIB_MARCH_VARIANT */

typedef enum
{
  COLOR_INPUT_NEXT_DROP,
  COLOR_INPUT_N_NEXT,
} CoLoR_input_next_t;

always_inline uword
CoLoR_input_inline (vlib_main_t *vm, vlib_node_runtime_t *node,
		    vlib_frame_t *frame, int is_ip4, int is_trace)
{
  u32 n_left_from, *from;
  vlib_buffer_t *bufs[VLIB_FRAME_SIZE], **b;
  u16 nexts[VLIB_FRAME_SIZE], *next;

  from = vlib_frame_vector_args (frame);
  n_left_from = frame->n_vectors;

  if (node->flags & VLIB_NODE_FLAG_TRACE)
    vlib_trace_frame_buffers_only (vm, node, from, frame->n_vectors, 0,
				   sizeof (CoLoR_input_trace_t));

  vlib_get_buffers (vm, from, bufs, n_left_from);
  b = bufs;
  next = nexts;

  while (n_left_from >= 4)
    {
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

      b += 4;
      next += 4;
      n_left_from -= 4;
    }

  while (n_left_from > 0)
    {

      /* $$$$ process 1 pkt right here */
      next[0] = 0;

      b += 1;
      next += 1;
      n_left_from -= 1;
    }

  vlib_buffer_enqueue_to_next (vm, node, from, nexts, frame->n_vectors);

  return frame->n_vectors;
}

VLIB_NODE_FN (CoLoR_input_node)
(vlib_main_t *vm, vlib_node_runtime_t *node, vlib_frame_t *frame)
{
  if (PREDICT_FALSE (node->flags & VLIB_NODE_FLAG_TRACE))
    return CoLoR_input_inline (vm, node, frame, 1 /* is_ip4 */,
			       1 /* is_trace */);
  else
    return CoLoR_input_inline (vm, node, frame, 1 /* is_ip4 */,
			       0 /* is_trace */);
}

/* *INDENT-OFF* */
#ifndef CLIB_MARCH_VARIANT
VLIB_REGISTER_NODE (CoLoR_input_node) = 
{
  .name = "CoLoR-input",
  .vector_size = sizeof (u32),
  .format_trace = format_CoLoR_input_trace,
  .type = VLIB_NODE_TYPE_INTERNAL,
  
  .n_errors = ARRAY_LEN(CoLoR_error_strings),
  .error_strings = CoLoR_error_strings,

  .n_next_nodes = COLOR_INPUT_N_NEXT,

  /* edit / add dispositions here */
  .next_nodes = {
        // [COLOR_INPUT_NEXT_DROP] = "error-drop",
        // TODO: fix error path
        [COLOR_INPUT_NEXT_DROP] = "CoLoR-output",
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
