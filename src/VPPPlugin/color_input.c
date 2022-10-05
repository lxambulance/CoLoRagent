/*
 * color-input node. filter bad NID SID, record valid packet to rx_buffer
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
  u16 next;
} color_input_trace_t;

#ifndef CLIB_MARCH_VARIANT

/* packet trace format function */
static u8 *
format_color_input_trace (u8 *s, va_list *args)
{
  CLIB_UNUSED (vlib_main_t * vm) = va_arg (*args, vlib_main_t *);
  CLIB_UNUSED (vlib_node_t * node) = va_arg (*args, vlib_node_t *);
  color_input_trace_t *t = va_arg (*args, color_input_trace_t *);

  u32 indent = format_get_indent (s);
  s = format (s, "%U\n", format_color_packet, t->packet_data);
  s = format (s, "%Unext node:", format_white_space, indent);
  if (t->next == 1)
    s = format (s, "app");
  else
    s = format (s, "drop");

  return s;
}

vlib_node_registration_t color_input_node;

#endif /* CLIB_MARCH_VARIANT */

typedef enum
{
  COLOR_INPUT_NEXT_DROP,
  COLOR_INPUT_N_NEXT,
} color_input_next_t;

always_inline uword
color_input_inline (vlib_main_t *vm, vlib_node_runtime_t *node,
		    vlib_frame_t *frame, int is_ip4, int is_trace)
{
  u32 n_left_from, n_to_next, *from, *f, *now_from;
  vlib_buffer_t *bufs[VLIB_FRAME_SIZE], **b;
  u16 nexts[VLIB_FRAME_SIZE], *next, *now_next;

  from = vlib_frame_vector_args (frame);
  n_left_from = frame->n_vectors;

  vlib_get_buffers (vm, from, bufs, n_left_from);
  b = bufs;
  next = nexts;

  f = from;
  now_from = from;
  now_next = next;
  n_to_next = 0;

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
      next[0] = next[1] = next[2] = next[3] = COLOR_INPUT_N_NEXT;

      if (is_trace)
	{
	  if (b[0]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_input_trace_t *t =
		vlib_add_trace (vm, node, b[0], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[0]),
				sizeof (t->packet_data));
	      t->next = next[0];
	    }
	  if (b[1]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_input_trace_t *t =
		vlib_add_trace (vm, node, b[1], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[1]),
				sizeof (t->packet_data));
	      t->next = next[1];
	    }
	  if (b[2]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_input_trace_t *t =
		vlib_add_trace (vm, node, b[2], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[2]),
				sizeof (t->packet_data));
	      t->next = next[2];
	    }
	  if (b[3]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_input_trace_t *t =
		vlib_add_trace (vm, node, b[3], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[3]),
				sizeof (t->packet_data));
	      t->next = next[3];
	    }
	}

      /* enqueue to color periodic */
      if (PREDICT_TRUE (next[0] == COLOR_INPUT_N_NEXT))
	{
	  color_rx_push_back (b[0]);
	}
      else
	{
	  now_next[0] = next[0];
	  now_next++;
	  now_from[0] = f[0];
	  now_from++;
	  n_to_next++;
	}
      if (PREDICT_TRUE (next[1] == COLOR_INPUT_N_NEXT))
	{
	  color_rx_push_back (b[1]);
	}
      else
	{
	  now_next[0] = next[1];
	  now_next++;
	  now_from[0] = f[1];
	  now_from++;
	  n_to_next++;
	}
      if (PREDICT_TRUE (next[2] == COLOR_INPUT_N_NEXT))
	{
	  color_rx_push_back (b[2]);
	}
      else
	{
	  now_next[0] = next[2];
	  now_next++;
	  now_from[0] = f[2];
	  now_from++;
	  n_to_next++;
	}
      if (PREDICT_TRUE (next[3] == COLOR_INPUT_N_NEXT))
	{
	  color_rx_push_back (b[3]);
	}
      else
	{
	  now_next[0] = next[3];
	  now_next++;
	  now_from[0] = f[3];
	  now_from++;
	  n_to_next++;
	}

      next += 4;
      f += 4;
      b += 4;
      n_left_from -= 4;
    }

  while (n_left_from > 0)
    {
      /* $$$$ process 1 pkt right here */
      next[0] = COLOR_INPUT_N_NEXT;

      if (is_trace)
	{
	  if (b[0]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_input_trace_t *t =
		vlib_add_trace (vm, node, b[0], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[0]),
				sizeof (t->packet_data));
	      t->next = next[0];
	    }
	}

      /* enqueue to color periodic */
      if (PREDICT_TRUE (next[0] == COLOR_INPUT_N_NEXT))
	{
	  color_rx_push_back (b[0]);
	}
      else
	{
	  now_next[0] = next[0];
	  now_next++;
	  now_from[0] = f[0];
	  now_from++;
	  n_to_next++;
	}

      next += 1;
      f += 1;
      b += 1;
      n_left_from -= 1;
    }

  vlib_buffer_enqueue_to_next (vm, node, from, nexts, n_to_next);

  if (n_to_next != frame->n_vectors)
    {
      color_main_t *Cmp = &color_main;
      color_create_periodic_process (Cmp);
      vlib_process_signal_event (Cmp->vlib_main, Cmp->periodic_node_index,
				 COLOR_EVENT2, (uword) 1);
    }

  return frame->n_vectors;
}

VLIB_NODE_FN (color_input_node)
(vlib_main_t *vm, vlib_node_runtime_t *node, vlib_frame_t *frame)
{
  if (PREDICT_FALSE (node->flags & VLIB_NODE_FLAG_TRACE))
    return color_input_inline (vm, node, frame, 1 /* is_ip4 */,
			       1 /* is_trace */);
  else
    return color_input_inline (vm, node, frame, 1 /* is_ip4 */,
			       0 /* is_trace */);
}

/* *INDENT-OFF* */
#ifndef CLIB_MARCH_VARIANT
VLIB_REGISTER_NODE (color_input_node) = 
{
  .name = "color-input",
  .vector_size = sizeof (u32),
  .format_trace = format_color_input_trace,
  .type = VLIB_NODE_TYPE_INTERNAL,
  
  .n_errors = ARRAY_LEN(color_error_strings),
  .error_strings = color_error_strings,

  .n_next_nodes = COLOR_INPUT_N_NEXT,

  /* edit / add dispositions here */
  .next_nodes = {
        [COLOR_INPUT_NEXT_DROP] = "drop",
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
