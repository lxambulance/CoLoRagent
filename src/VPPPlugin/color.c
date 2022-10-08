/*
 * color.c - skeleton vpp engine plug-in
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

#include <vnet/vnet.h>
#include <vnet/plugin/plugin.h>
#include <color/color.h>

#include <vlibapi/api.h>
#include <vlibmemory/api.h>
#include <vpp/app/version.h>
#include <stdbool.h>

#include <color/color.api_enum.h>
#include <color/color.api_types.h>

#define REPLY_MSG_ID_BASE Cmp->msg_id_base
#include <vlibapi/api_helper_macros.h>

color_main_t color_main;

/* this format need three args:
  buffer pointer(color_header_t *),
  max_buffer_length(u32),
  valid_checksum(int) */
u8 *
format_color_header (u8 *s, va_list *args)
{
  color_header_t *ch = va_arg (*args, color_header_t *);
  u32 max_header_length = va_arg (*args, u32);
  u16 valid_checksum = va_arg (*args, int);
  u32 indent;

  if (max_header_length < sizeof (color_header_t))
    return format (s, "color header truncated");

  indent = format_get_indent (s);
  
  s = format (s, "color protocol\n");

#ifndef NDEBUG
  u8 *start = (u8 *) ch;
  int i;
  s = format (s, "%Uorigin string:", format_white_space, indent);
  u32 slen = max_header_length < ch->packet_length ? max_header_length :
							   ch->packet_length;
  for (i = 0; i < slen; ++i)
    s = format (s, "%02x", start[i]);
  s = format (s, "\n");
#endif

  u8 V = get_color_version (ch->color_version_and_packet_type);
  u8 T = get_packet_type (ch->color_version_and_packet_type);
  s = format (s, "%UVersion %d, Type %s\n", format_white_space, indent, V,
	      color_packet_type_strings[T]);
  indent += 2;

  s = format (s, "%Uttl %d, packet_length %d, checksum 0x%04x",
	      format_white_space, indent, ch->ttl, ch->packet_length,
	      ch->checksum);
  // ignore control packet for now
  if (T != 3&&ch->checksum != valid_checksum)
    s = format (s, "(should be 0x%04x)", valid_checksum);

  return s;
}

/* Action function shared between message handler and debug CLI */

int
color_enable_disable (color_main_t *Cmp, u32 sw_if_index, int enable_disable)
{
  vnet_sw_interface_t *sw;
  int rv = 0;

  /* Utterly wrong? */
  if (pool_is_free_index (Cmp->vnet_main->interface_main.sw_interfaces,
			  sw_if_index))
    return VNET_API_ERROR_INVALID_SW_IF_INDEX;

  /* Not a physical port? */
  sw = vnet_get_sw_interface (Cmp->vnet_main, sw_if_index);
  if (sw->type != VNET_SW_INTERFACE_TYPE_HARDWARE)
    return VNET_API_ERROR_INVALID_SW_IF_INDEX;

  color_create_periodic_process (Cmp);

  vnet_feature_enable_disable ("device-input", "color", sw_if_index,
			       enable_disable, 0, 0);

  /* Send an event to enable/disable the periodic scanner process */
  // vlib_process_signal_event (Cmp->vlib_main, Cmp->periodic_node_index,
  // 		     COLOR_EVENT_PERIODIC_ENABLE_DISABLE,
  // 		     (uword) enable_disable);
  vlib_process_signal_event (Cmp->vlib_main, Cmp->periodic_node_index,
			     COLOR_EVENT1, (uword) 3);
  return rv;
}

static clib_error_t *
color_enable_disable_command_fn (vlib_main_t *vm, unformat_input_t *input,
				 vlib_cli_command_t *cmd)
{
  color_main_t *Cmp = &color_main;
  u32 sw_if_index = ~0;
  int enable_disable = 1;

  int rv;

  while (unformat_check_input (input) != UNFORMAT_END_OF_INPUT)
    {
      if (unformat (input, "disable"))
	enable_disable = 0;
      else if (unformat (input, "%U", unformat_vnet_sw_interface,
			 Cmp->vnet_main, &sw_if_index))
	;
      else
	break;
    }

  if (sw_if_index == ~0)
    return clib_error_return (0, "Please specify an interface...");

  rv = color_enable_disable (Cmp, sw_if_index, enable_disable);

  switch (rv)
    {
    case 0:
      break;

    case VNET_API_ERROR_INVALID_SW_IF_INDEX:
      return clib_error_return (
	0, "Invalid interface, only works on physical ports");
      break;

    case VNET_API_ERROR_UNIMPLEMENTED:
      return clib_error_return (0,
				"Device driver doesn't support redirection");
      break;

    default:
      return clib_error_return (0, "color_enable_disable returned %d", rv);
    }
  return 0;
}

/* *INDENT-OFF* */
VLIB_CLI_COMMAND (color_enable_disable_command, static) = {
  .path = "color enable-disable",
  .short_help = "color enable-disable <interface-name> [disable]",
  .function = color_enable_disable_command_fn,
};
/* *INDENT-ON* */

/* API message handler */
static void
vl_api_color_enable_disable_t_handler (vl_api_color_enable_disable_t *mp)
{
  vl_api_color_enable_disable_reply_t *rmp;
  color_main_t *Cmp = &color_main;
  int rv;

  rv = color_enable_disable (Cmp, ntohl (mp->sw_if_index),
			     (int) (mp->enable_disable));

  REPLY_MACRO (VL_API_COLOR_ENABLE_DISABLE_REPLY);
}

/* API definitions */
#include <color/color.api.c>

static clib_error_t *
color_init (vlib_main_t *vm)
{
  color_main_t *Cmp = &color_main;
  clib_error_t *error = 0;

  Cmp->vlib_main = vm;
  Cmp->vnet_main = vnet_get_main ();

  /* Add our API messages to the global name_crc hash table */
  Cmp->msg_id_base = setup_message_id_table ();

  /* register color protocol in ip4 node */
  ip4_register_protocol (150, color_lookup_node.index);

  /* set tx/rx buffers to NULL */
  Cmp->tx_buffers = NULL;
  Cmp->rx_fifo_queue = NULL;
  clib_fifo_validate(Cmp->rx_fifo_queue, RX_LIMIT);

  return error;
}

VLIB_INIT_FUNCTION (color_init);

/* *INDENT-OFF* */
VLIB_PLUGIN_REGISTER () = {
  .version = VPP_BUILD_VER,
  .description = "color protocol plugin, make your network secure and easy in "
		 "inter-domain connection",
};
/* *INDENT-ON* */

/*
 * fd.io coding-style-patch-verification: ON
 *
 * Local Variables:
 * eval: (c-set-style "gnu")
 * End:
 */
