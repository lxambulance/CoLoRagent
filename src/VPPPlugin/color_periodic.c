/*
 * color_periodic.c - skeleton plug-in periodic function
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
#include <vnet/ip/ip4.h>

#include <color/color.h>
#include <color/color_packet.h>

static void
handle_event1 (color_main_t *pm, f64 now, uword event_data)
{
  clib_warning ("received COLOR_EVENT1 %d\n", event_data);
  vlib_main_t *vm = pm->vlib_main;
  u32 current_length = vec_len (pm->tx_buffers);
  u32 packet_need_to_send = 256;

  // clib_warning ("COLOR_EVENT1 step1\n");
  vec_validate (pm->tx_buffers, current_length + packet_need_to_send - 1);
  // clib_warning ("COLOR_EVENT1 step2\n");
  u32 *buffer_start = &pm->tx_buffers[current_length];
  u32 n_allocated = vlib_buffer_alloc (vm, buffer_start, packet_need_to_send);
  // clib_warning ("COLOR_EVENT1 step3\n");
  _vec_len (pm->tx_buffers) = current_length + n_allocated;

  clib_warning ("COLOR_EVENT1 buffer_alloc %d\n", n_allocated);

  int i;
  u8 n_sid[30], l_sid[30], nid[30];
  u8 data[1000];
  for (i = 0; i < n_allocated; ++i)
    {
      vlib_buffer_t *b0;
      ip4_header_t *ip;
      u8 *cd;

      b0 = vlib_get_buffer (vm, buffer_start[i]);
      ip = vlib_buffer_get_current (b0);
      cd = (u8 *) (ip + 1);

      // n_sid[i % 16] = l_sid[i % 20] = nid[i % 16] = data[i % 1000] = i %
      // 256;
      DATA_init (cd, n_sid, l_sid, nid);
      DATA_append_pid (cd, 0x1122ffff);
      DATA_append_pid (cd, 0x3344ffff);
      // DATA_append_pid (cd, 0);
      // ((DATA_header_t *) cd)->PID_pt -= 1;
      // ((DATA_header_t *) cd)->PID_num -= 1;
      DATA_append_data (cd, data, 0);
      // ((DATA_header_t *) cd)->flag |= 0x20;
      // TODO: move calculate checksum to color_output node
      DATA_update_checksum (cd);

      ip->ip_version_and_header_length = 0x45;
      ip->ttl = 254;
      ip->protocol = 150;
      ip->length =
	clib_host_to_net_u16 (sizeof (*ip) + ((DATA_header_t *) cd)->pkt_len);
      ip->src_address.data[0] = 10;
      ip->src_address.data[1] = 10;
      ip->src_address.data[2] = 10;
      ip->src_address.data[3] = 1;
      ip->dst_address.data[0] = 10;
      ip->dst_address.data[1] = 10;
      ip->dst_address.data[2] = 10;
      ip->dst_address.data[3] = 2;
      ip->fragment_id = clib_host_to_net_u16 (i);
      ip->flags_and_fragment_offset =
	clib_host_to_net_u16 (IP4_HEADER_FLAG_DONT_FRAGMENT);
      ip->checksum = ip4_header_checksum (ip);

      vnet_buffer (b0)->sw_if_index[VLIB_RX] = 0;
      vnet_buffer (b0)->sw_if_index[VLIB_TX] = 0;
      b0->current_length = sizeof (*ip) + ((DATA_header_t *) cd)->pkt_len;
      b0->flags |= VLIB_BUFFER_TOTAL_LENGTH_VALID;
    }

  vlib_frame_t *f;
  f = vlib_get_frame_to_node (vm, ip4_lookup_node.index);
  u32 max_frame_size =
    n_allocated > 256 - f->n_vectors ? 256 - f->n_vectors : n_allocated;
  u32 *to_next = vlib_frame_vector_args (f);

  for (i = 0; i < max_frame_size; i++)
    to_next[i + f->n_vectors] = buffer_start[i];
  f->n_vectors += max_frame_size;
  clib_warning ("frame buffer send %d\n", max_frame_size);

  vlib_put_frame_to_node (vm, ip4_lookup_node.index, f);

  f64 end = vlib_time_now (vm);
  clib_warning ("speed(pkts/second): %.5f time[%.5f,%.5f]\n",
		(f64) n_allocated / (end - now), now, end);
}

static void
handle_event2 (color_main_t *pm, f64 now, uword event_data)
{
  clib_warning ("received COLOR_EVENT2%d\n", event_data);
}

static void
handle_periodic_enable_disable (color_main_t *pm, f64 now, uword event_data)
{
  clib_warning ("Periodic timeouts now %s",
		event_data ? "enabled" : "disabled");
  pm->periodic_timer_enabled = event_data;
}

static void
handle_timeout (color_main_t *pm, f64 now)
{
  clib_warning ("timeout at %.2f", now);
}

static uword
color_periodic_process (vlib_main_t *vm, vlib_node_runtime_t *rt,
			vlib_frame_t *f)
{
  color_main_t *pm = &color_main;
  f64 now;
  f64 timeout = 10.0;
  uword *event_data = 0;
  uword event_type;
  int i;

  while (1)
    {
      if (pm->periodic_timer_enabled)
	vlib_process_wait_for_event_or_clock (vm, timeout);
      else
	vlib_process_wait_for_event (vm);

      now = vlib_time_now (vm);

      event_type = vlib_process_get_events (vm, (uword **) &event_data);

      switch (event_type)
	{
	  /* Handle COLOR_EVENT1 */
	case COLOR_EVENT1:
	  for (i = 0; i < vec_len (event_data); i++)
	    handle_event1 (pm, now, event_data[i]);
	  break;

	  /* Handle COLOR_EVENT2 */
	case COLOR_EVENT2:
	  for (i = 0; i < vec_len (event_data); i++)
	    handle_event2 (pm, now, event_data[i]);
	  break;
	  /* Handle the periodic timer on/off event */
	case COLOR_EVENT_PERIODIC_ENABLE_DISABLE:
	  for (i = 0; i < vec_len (event_data); i++)
	    handle_periodic_enable_disable (pm, now, event_data[i]);
	  break;

	  /* Handle periodic timeouts */
	case ~0:
	  handle_timeout (pm, now);
	  break;
	}
      vec_reset_length (event_data);
    }
  return 0; /* or not */
}

void
color_create_periodic_process (color_main_t *Cmp)
{
  /* Already created the process node? */
  if (Cmp->periodic_node_index > 0)
    return;

  /* No, create it now and make a note of the node index */
  Cmp->periodic_node_index =
    vlib_process_create (Cmp->vlib_main, "color-periodic-process",
			 color_periodic_process, 16 /* log2_n_stack_bytes */);
}

/*
 * fd.io coding-style-patch-verification: ON
 *
 * Local Variables:
 * eval: (c-set-style "gnu")
 * End:
 */
