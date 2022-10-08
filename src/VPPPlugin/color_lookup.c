/*
 * color-lookup node. check checksum, TTL, packet length
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
#include <vppinfra/error.h>
#include <vnet/ip/ip4_packet.h>

#include <color/color.h>
#include <color/color_packet.h>

typedef struct
{
  u8 packet_data[160];
  u16 valid_checksum;
} color_lookup_trace_t;

#ifndef CLIB_MARCH_VARIANT

/* packet trace format function */
static u8 *
format_color_lookup_trace (u8 *s, va_list *args)
{
  CLIB_UNUSED (vlib_main_t * vm) = va_arg (*args, vlib_main_t *);
  CLIB_UNUSED (vlib_node_t * node) = va_arg (*args, vlib_node_t *);
  color_lookup_trace_t *t = va_arg (*args, color_lookup_trace_t *);

  s = format (s, "%U", format_color_header, t->packet_data,
	      sizeof (t->packet_data), (int) t->valid_checksum);

  return s;
}

vlib_node_registration_t color_lookup_node;

#endif /* CLIB_MARCH_VARIANT */

typedef enum
{
  COLOR_LOOKUP_NEXT_DROP,
  COLOR_LOOKUP_NEXT_INPUT,
  COLOR_LOOKUP_N_NEXT,
} color_lookup_next_t;

always_inline void
check_color_packet_x4 (vlib_node_runtime_t *error_node, vlib_buffer_t **buf,
		       u16 *next, u16 *valid_checksum)
{
  ip4_header_t *ip0, *ip1, *ip2, *ip3;
  color_header_t *c0, *c1, *c2, *c3;
  u8 error0, error1, error2, error3;

  error0 = error1 = error2 = error3 = 0;

  ip0 = (ip4_header_t *) vlib_buffer_get_current (buf[0]);
  ip1 = (ip4_header_t *) vlib_buffer_get_current (buf[1]);
  ip2 = (ip4_header_t *) vlib_buffer_get_current (buf[2]);
  ip3 = (ip4_header_t *) vlib_buffer_get_current (buf[3]);
  c0 = (color_header_t *) (ip0 + 1);
  c1 = (color_header_t *) (ip1 + 1);
  c2 = (color_header_t *) (ip2 + 1);
  c3 = (color_header_t *) (ip3 + 1);

  if (PREDICT_FALSE (c0->packet_length !=
		     clib_net_to_host_u16 (ip0->length) - 20))
    error0 = COLOR_ERROR_BAD_LENGTH;
  if (PREDICT_FALSE (c1->packet_length !=
		     clib_net_to_host_u16 (ip1->length) - 20))
    error1 = COLOR_ERROR_BAD_LENGTH;
  if (PREDICT_FALSE (c2->packet_length !=
		     clib_net_to_host_u16 (ip2->length) - 20))
    error2 = COLOR_ERROR_BAD_LENGTH;
  if (PREDICT_FALSE (c3->packet_length !=
		     clib_net_to_host_u16 (ip3->length) - 20))
    error3 = COLOR_ERROR_BAD_LENGTH;

  if (PREDICT_FALSE (c0->ttl < 1))
    error0 = error0 ? error0 : COLOR_ERROR_TIME_EXPIRED;
  if (PREDICT_FALSE (c1->ttl < 1))
    error1 = error1 ? error1 : COLOR_ERROR_TIME_EXPIRED;
  if (PREDICT_FALSE (c2->ttl < 1))
    error2 = error2 ? error2 : COLOR_ERROR_TIME_EXPIRED;
  if (PREDICT_FALSE (c3->ttl < 1))
    error3 = error3 ? error3 : COLOR_ERROR_TIME_EXPIRED;

  u16 tmp0 = c0->checksum;
  u16 tmp1 = c1->checksum;
  u16 tmp2 = c2->checksum;
  u16 tmp3 = c3->checksum;
  c0->checksum = c1->checksum = c2->checksum = c3->checksum = 0;
  u8 header_len0 = get_packet_type (c0->color_version_and_packet_type) != 2 ?
		     c0->packet_length :
		     *((u8 *) (c0 + 1));
  u8 header_len1 = get_packet_type (c1->color_version_and_packet_type) != 2 ?
		     c1->packet_length :
		     *((u8 *) (c1 + 1));
  u8 header_len2 = get_packet_type (c2->color_version_and_packet_type) != 2 ?
		     c2->packet_length :
		     *((u8 *) (c2 + 1));
  u8 header_len3 = get_packet_type (c3->color_version_and_packet_type) != 2 ?
		     c3->packet_length :
		     *((u8 *) (c3 + 1));
  valid_checksum[0] = calculate_checksum ((u16 *) c0, header_len0);
  valid_checksum[1] = calculate_checksum ((u16 *) c1, header_len1);
  valid_checksum[2] = calculate_checksum ((u16 *) c2, header_len2);
  valid_checksum[3] = calculate_checksum ((u16 *) c3, header_len3);
  c0->checksum = tmp0;
  c1->checksum = tmp1;
  c2->checksum = tmp2;
  c3->checksum = tmp3;

  if (PREDICT_FALSE (c0->checksum != valid_checksum[0]))
    error0 = error0 ? error0 : COLOR_ERROR_BAD_CHECKSUM;
  if (PREDICT_FALSE (c1->checksum != valid_checksum[1]))
    error1 = error1 ? error1 : COLOR_ERROR_BAD_CHECKSUM;
  if (PREDICT_FALSE (c2->checksum != valid_checksum[2]))
    error2 = error2 ? error2 : COLOR_ERROR_BAD_CHECKSUM;
  if (PREDICT_FALSE (c3->checksum != valid_checksum[3]))
    error3 = error3 ? error3 : COLOR_ERROR_BAD_CHECKSUM;

  if (PREDICT_FALSE (error0 != COLOR_ERROR_NONE))
    {
      next[0] = COLOR_LOOKUP_NEXT_DROP;
      buf[0]->error = error_node->errors[error0];
    }
  if (PREDICT_FALSE (error1 != COLOR_ERROR_NONE))
    {
      next[1] = COLOR_LOOKUP_NEXT_DROP;
      buf[1]->error = error_node->errors[error1];
    }
  if (PREDICT_FALSE (error2 != COLOR_ERROR_NONE))
    {
      next[2] = COLOR_LOOKUP_NEXT_DROP;
      buf[2]->error = error_node->errors[error2];
    }
  if (PREDICT_FALSE (error3 != COLOR_ERROR_NONE))
    {
      next[3] = COLOR_LOOKUP_NEXT_DROP;
      buf[3]->error = error_node->errors[error3];
    }
  // ignore control packet for now
  if (get_packet_type (c0->color_version_and_packet_type) == 3)
    next[0] = COLOR_LOOKUP_NEXT_INPUT;
  if (get_packet_type (c1->color_version_and_packet_type) == 3)
    next[1] = COLOR_LOOKUP_NEXT_INPUT;
  if (get_packet_type (c2->color_version_and_packet_type) == 3)
    next[2] = COLOR_LOOKUP_NEXT_INPUT;
  if (get_packet_type (c3->color_version_and_packet_type) == 3)
    next[3] = COLOR_LOOKUP_NEXT_INPUT;
}

always_inline void
check_color_packet (vlib_node_runtime_t *error_node, vlib_buffer_t **buf,
		    u16 *next, u16 *valid_checksum)
{
  ip4_header_t *ip = (ip4_header_t *) vlib_buffer_get_current (buf[0]);
  color_header_t *c = (color_header_t *) (ip + 1);

  // clib_warning ("color length=%d ip length=%d\n", c->packet_length,
  // 	clib_net_to_host_u16 (ip->length));

  if (PREDICT_FALSE (c->packet_length !=
		     clib_net_to_host_u16 (ip->length) - 20))
    {
      if (next[0] > 0)
	{
	  next[0] = COLOR_LOOKUP_NEXT_DROP;
	  buf[0]->error = error_node->errors[COLOR_ERROR_BAD_LENGTH];
	}
    }

  if (PREDICT_FALSE (c->ttl < 1))
    {
      if (next[0] > 0)
	{
	  next[0] = COLOR_LOOKUP_NEXT_DROP;
	  buf[0]->error = error_node->errors[COLOR_ERROR_TIME_EXPIRED];
	}
    }

  u16 tmp = c->checksum;
  c->checksum = 0;
  u8 header_len = get_packet_type (c->color_version_and_packet_type) != 2 ?
		    c->packet_length :
		    *((u8 *) (c + 1));
  valid_checksum[0] = calculate_checksum ((u16 *) c, header_len);
  c->checksum = tmp;

  if (PREDICT_FALSE (c->checksum != valid_checksum[0]))
    {
      if (next[0] > 0)
	{
	  next[0] = COLOR_LOOKUP_NEXT_DROP;
	  buf[0]->error = error_node->errors[COLOR_ERROR_BAD_CHECKSUM];
	}
    }
  // ignore control packet for now
  if (get_packet_type (c->color_version_and_packet_type) == 3)
    next[0] = COLOR_LOOKUP_NEXT_INPUT;
}

always_inline uword
color_lookup_inline (vlib_main_t *vm, vlib_node_runtime_t *node,
		     vlib_frame_t *frame, int is_ip4, int is_trace)
{
  u32 n_left_from, *from;
  vlib_buffer_t *bufs[VLIB_FRAME_SIZE], **b;
  u16 nexts[VLIB_FRAME_SIZE], *next;
  vlib_node_runtime_t *error_node =
    vlib_node_get_runtime (vm, color_input_node.index);

  from = vlib_frame_vector_args (frame);
  n_left_from = frame->n_vectors;

  vlib_get_buffers (vm, from, bufs, n_left_from);
  b = bufs;
  next = nexts;

  u16 valid_checksum[4];

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
      next[0] = next[1] = next[2] = next[3] = COLOR_LOOKUP_NEXT_INPUT;
      check_color_packet_x4 (error_node, b, next, valid_checksum);

      /* ignore ip header */
      vlib_buffer_advance (b[0], 20);
      vlib_buffer_advance (b[1], 20);
      vlib_buffer_advance (b[2], 20);
      vlib_buffer_advance (b[3], 20);

      if (is_trace)
	{
	  if (b[0]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_lookup_trace_t *t =
		vlib_add_trace (vm, node, b[0], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[0]),
				sizeof (t->packet_data));
	      t->valid_checksum = valid_checksum[0];
	    }
	  if (b[1]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_lookup_trace_t *t =
		vlib_add_trace (vm, node, b[1], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[1]),
				sizeof (t->packet_data));
	      t->valid_checksum = valid_checksum[1];
	    }
	  if (b[2]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_lookup_trace_t *t =
		vlib_add_trace (vm, node, b[2], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[2]),
				sizeof (t->packet_data));
	      t->valid_checksum = valid_checksum[2];
	    }
	  if (b[3]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_lookup_trace_t *t =
		vlib_add_trace (vm, node, b[3], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[3]),
				sizeof (t->packet_data));
	      t->valid_checksum = valid_checksum[3];
	    }
	}
      b += 4;
      next += 4;
      n_left_from -= 4;
    }

  while (n_left_from > 0)
    {
      /* $$$$ process 1 pkt right here */
      next[0] = COLOR_LOOKUP_NEXT_INPUT;
      check_color_packet (error_node, b, next, valid_checksum);

      /* ignore ip header */
      vlib_buffer_advance (b[0], 20);

      if (is_trace)
	{
	  if (b[0]->flags & VLIB_BUFFER_IS_TRACED)
	    {
	      color_lookup_trace_t *t =
		vlib_add_trace (vm, node, b[0], sizeof (*t));
	      clib_memcpy_fast (t->packet_data, vlib_buffer_get_current (b[0]),
				sizeof (t->packet_data));
	      t->valid_checksum = valid_checksum[0];
	    }
	}

      b += 1;
      next += 1;
      n_left_from -= 1;
    }

  vlib_buffer_enqueue_to_next (vm, node, from, nexts, frame->n_vectors);

  return frame->n_vectors;
}

VLIB_NODE_FN (color_lookup_node)
(vlib_main_t *vm, vlib_node_runtime_t *node, vlib_frame_t *frame)
{
  if (PREDICT_FALSE (node->flags & VLIB_NODE_FLAG_TRACE))
    return color_lookup_inline (vm, node, frame, 1 /* is_ip4 */,
				1 /* is_trace */);
  else
    return color_lookup_inline (vm, node, frame, 1 /* is_ip4 */,
				0 /* is_trace */);
}

/* *INDENT-OFF* */
#ifndef CLIB_MARCH_VARIANT
VLIB_REGISTER_NODE (color_lookup_node) = 
{
  .name = "color-lookup",
  .vector_size = sizeof (u32),
  .format_trace = format_color_lookup_trace,
  .type = VLIB_NODE_TYPE_INTERNAL,
  
  .n_errors = ARRAY_LEN(color_error_strings),
  .error_strings = color_error_strings,

  .n_next_nodes = COLOR_LOOKUP_N_NEXT,

  /* edit / add dispositions here */
  .next_nodes = {
        [COLOR_LOOKUP_NEXT_DROP] = "drop",
        [COLOR_LOOKUP_NEXT_INPUT] = "color-input",
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
