#include <color/color_packet.h>

/* ---color checksum--- */

// 1 for good, 0 for bad
always_inline int
check_checksum (u16 *buf, u16 count)
{
  return (calculate_checksum (buf, count) == 0xffff) ? 1 : 0;
}

int
ANN_check_checksum (u8 *buf)
{
  if (!buf)
    return -1;
  ANN_header_t *ann_pt = (ANN_header_t *) buf;
  return check_checksum ((u16 *) buf, ann_pt->pkt_len);
}

void
ANN_update_checksum (u8 *buf)
{
  if (!buf)
    return;
  ANN_header_t *ann_pt = (ANN_header_t *) buf;
  ann_pt->checksum = 0;
  ann_pt->checksum = calculate_checksum ((u16 *) buf, ann_pt->pkt_len);
}

int
GET_check_checksum (u8 *buf)
{
  if (!buf)
    return -1;
  GET_header_t *get_pt = (GET_header_t *) buf;
  return check_checksum ((u16 *) buf, get_pt->pkt_len);
}

void
GET_update_checksum (u8 *buf)
{
  if (!buf)
    return;
  GET_header_t *get_pt = (GET_header_t *) buf;
  get_pt->checksum = 0;
  get_pt->checksum = calculate_checksum ((u16 *) buf, get_pt->pkt_len);
}

int
DATA_check_checksum (u8 *buf)
{
  if (!buf)
    return -1;
  DATA_header_t *data_pt = (DATA_header_t *) buf;
  return check_checksum ((u16 *) buf, data_pt->header_len);
}

void
DATA_update_checksum (u8 *buf)
{
  if (!buf)
    return;
  DATA_header_t *data_pt = (DATA_header_t *) buf;
  data_pt->checksum = 0;
  data_pt->checksum = calculate_checksum ((u16 *) buf, data_pt->header_len);
}

int
CONTROL_check_checksum (u8 *buf)
{
  if (!buf)
    return -1;
  CONTROL_header_t *con_pt = (CONTROL_header_t *) buf;
  return check_checksum ((u16 *) buf, con_pt->header_len);
}

void
CONTROL_update_checksum (u8 *buf)
{
  if (!buf)
    return;
  CONTROL_header_t *con_pt = (CONTROL_header_t *) buf;
  con_pt->checksum = 0;
  con_pt->checksum = calculate_checksum ((u16 *) buf, con_pt->header_len);
}

// initialize the header part of the ANN pkt
void
ANN_init (u8 *buf)
{
  if (!buf)
    return;
  ANN_header_t *ann_pt = (ANN_header_t *) buf;
  ann_pt->version_package = 0x71;
  ann_pt->ttl = DEFAULT_TTL;
  ann_pt->pkt_len = sizeof (ANN_header_t);
  ann_pt->checksum = 0;
  ann_pt->flag = 0;
  ann_pt->unit_px_num = 0;
}

// append a unit to ANN
void
ANN_append_unit (u8 *buf, u8 *unit)
{
  if (!buf || !unit)
    return;

  ANN_header_t *ann_pt = (ANN_header_t *) buf;
  ANN_unit_header_t *new_unit = (ANN_unit_header_t *) unit;

  // copy unit to ann tail
  clib_memcpy_fast (buf + ann_pt->pkt_len, (u8 *) new_unit,
		    new_unit->unit_len);

  ann_pt->pkt_len += new_unit->unit_len;
  ADD_ANN_UNIT_NUM (ann_pt->unit_px_num);
}

// initialize a unit, with SID and nid
void
ANN_unit_construct (u8 *buf, u8 *n_sid, u8 *l_sid, u8 *nid)
{
  if (!buf)
    return;

  ANN_unit_header_t *unit_pt = (ANN_unit_header_t *) buf;
  u8 offset = sizeof (ANN_unit_header_t);
  unit_pt->flag = 0;
  unit_pt->strategy_num = 0;

  // append SID and NID
  if (NULL != n_sid)
    {
      SET_ANN_UNIT_FLAG_N (unit_pt->flag);
      clib_memcpy_fast (buf + offset, n_sid, COLOR_N_SID_LEN);
      offset += COLOR_N_SID_LEN;
    }

  if (NULL != l_sid)
    {
      SET_ANN_UNIT_FLAG_L (unit_pt->flag);
      clib_memcpy_fast (buf + offset, l_sid, COLOR_L_SID_LEN);
      offset += COLOR_L_SID_LEN;
    }

  if (NULL != nid)
    {
      SET_ANN_UNIT_FLAG_I (unit_pt->flag);
      clib_memcpy_fast (buf + offset, nid, COLOR_NID_LEN);
      offset += COLOR_NID_LEN;
    }

  unit_pt->unit_len = offset;
}

// append strategy unit to unit buf
void
ANN_unit_append_strategy (u8 *buf, u8 t, u8 l, u8 *v)
{
  if (!buf || l <= 0 || !v)
    return;

  ANN_unit_header_t *unit_pt = (ANN_unit_header_t *) buf;
  u8 offset = unit_pt->unit_len;

  *((u8 *) (buf + offset)) = t;	    // t
  *((u8 *) (buf + offset + 1)) = l; // l

  clib_memcpy_fast (buf + offset + 2, v, l); // v

  unit_pt->unit_len += 2 + l;
  unit_pt->strategy_num += 1;
}

// append PX to the tail of ANN
void
ANN_append_px (u8 *buf, u16 px)
{
  if (!buf)
    return;

  ANN_header_t *ann_t = (ANN_header_t *) buf;
  *(u16 *) (buf + ann_t->pkt_len) = px;
  ann_t->pkt_len += 2;
  ADD_ANN_PX_NUM (ann_t->unit_px_num);
}

// initialize the header of the GET pkt
void
GET_init (u8 *buf, u8 *n_sid, u8 *l_sid, u8 *nid)
{
  if (!buf || !n_sid || !l_sid || !nid)
    return;

  GET_header_t *get_pt = (GET_header_t *) buf;
  get_pt->version_package = 0x72;
  get_pt->ttl = DEFAULT_TTL;
  get_pt->pkt_len = sizeof (GET_header_t);
  get_pt->checksum = 0;
  get_pt->MTU = 0;
  get_pt->PID_num = 0;
  get_pt->flag = 0;
  get_pt->Minimal_PID_CP = 0;

  clib_memcpy_fast (get_pt->N_sid, n_sid, COLOR_N_SID_LEN);
  clib_memcpy_fast (get_pt->L_sid, l_sid, COLOR_L_SID_LEN);
  clib_memcpy_fast (get_pt->nid, nid, COLOR_NID_LEN);
}

// append PID to the tail of GET
void
GET_append_pid (u8 *buf, u32 pid)
{
  if (!buf)
    return;

  GET_header_t *get_pt = (GET_header_t *) buf;
  *(u32 *) (buf + get_pt->pkt_len) = pid;
  get_pt->pkt_len += 4;
  get_pt->PID_num += 1;
}

// initialize the header of the DATA pkt
void
DATA_init (u8 *buf, u8 *n_sid, u8 *l_sid, u8 *nid)
{
  if (!buf || !n_sid || !l_sid || !nid)
    return;

  DATA_header_t *data_pt = (DATA_header_t *) buf;
  data_pt->version_package = 0x73;
  data_pt->ttl = DEFAULT_TTL;
  data_pt->pkt_len = sizeof (DATA_header_t);
  data_pt->checksum = 0;
  data_pt->header_len = data_pt->pkt_len;
  data_pt->PID_pt = 0;
  data_pt->PID_num = 0;
  data_pt->flag = 0;

  clib_memcpy_fast (data_pt->N_sid, n_sid, COLOR_N_SID_LEN);
  clib_memcpy_fast (data_pt->L_sid, l_sid, COLOR_L_SID_LEN);
  clib_memcpy_fast (data_pt->nid, nid, COLOR_NID_LEN);
}

// append PID to the tail of DATA
// must consider about data behind header!
void
DATA_append_pid (u8 *buf, u32 pid)
{
  if (!buf)
    return;

  DATA_header_t *data_pt = (DATA_header_t *) buf;
  *(u32 *) (buf + data_pt->pkt_len) = pid;
  data_pt->pkt_len += 4;
  data_pt->header_len = data_pt->pkt_len;
  data_pt->PID_pt += 1;
  data_pt->PID_num += 1;
}

// append payload to DATA
void
DATA_append_data (u8 *buf, u8 *data, int len)
{
  if (!buf || !data || len <= 0)
    return;

  DATA_header_t *data_pt = (DATA_header_t *) buf;

  clib_memcpy_fast (buf + data_pt->pkt_len, data, len);

  data_pt->pkt_len += len;
}

void
CONTROL_init (u8 *buf, u8 tag, u16 len, u8 *con_data)
{
  if (!buf)
    return;
  CONTROL_header_t *con_pt = (CONTROL_header_t *) buf;
  con_pt->version_package = 0x74;
  con_pt->ttl = DEFAULT_TTL;
  con_pt->header_len = sizeof (CONTROL_header_t);
  con_pt->tag = tag;
  con_pt->len = len;

#ifdef DPDK_RTE
  clib_memcpy_fast (buf + sizeof (CONTROL_header_t), con_data, len);
#else
  memcpy (buf + sizeof (CONTROL_header_t), con_data, len);
#endif
}

/* ------------------------------tool
 * function---------------------------------- */

// get package protocol
int
color_get_pkt_protocol (u8 *buf)
{
  if (!buf)
    return -1;
  else
    return GET_PROTOCOL_TYPE (buf[0]);
}

// get package type
int
color_get_pkt_type (u8 *buf)
{
  if (!buf)
    return -1;
  else
    return GET_PACKAGE_TYPE (buf[0]);
}

// get package length
int
color_get_pkt_length (u8 *buf)
{
  switch (color_get_pkt_type (buf))
    {
    case COLOR_ANN_TYPE:
      {
	return (((ANN_header_t *) buf))->pkt_len;
      }
    case COLOR_GET_TYPE:
      {
	return (((GET_header_t *) buf))->pkt_len;
      }
    case COLOR_DATA_TYPE:
      {
	return (((DATA_header_t *) buf))->pkt_len;
      }
    default:
      return -1;
    }
}

/* ---format color packet--- */

always_inline u8 *
format_fixedlength_string (u8 *s, va_list *args)
{
  u8 *buf = va_arg (*args, u8 *);
  int count = va_arg (*args, int);
  int i;
  for (i = 0; i < count; ++i)
    s = format (s, "%02x", buf[i]);
  return s;
}

always_inline u8 *
format_color_ann (u8 *s, va_list *args)
{
  u8 *buf = va_arg (*args, u8 *);
  if (!buf)
    return s;

  ANN_header_t *ann_pt = (ANN_header_t *) buf;
  ANN_unit_header_t *unit_pt;

  int i, j, offset = sizeof (ANN_header_t);
  int unit_num = GET_ANN_UNIT_NUM (ann_pt->unit_px_num),
      px_num = GET_ANN_PX_NUM (ann_pt->unit_px_num);
  u8 s_len;
  u32 indent = format_get_indent (s);

  // show the head of ANN
  s = format (
    s,
    "color ANN apcket\n%Upacket_length %d,flag %02x,unit_num %d,px_num %d\n",
    format_white_space, indent, ann_pt->pkt_len, ann_pt->checksum,
    ann_pt->flag, unit_num, px_num);

  indent += 2;
  // show the units in ANN
  for (i = 0; i < unit_num; i++)
    {
      u32 now_indent = indent;
      unit_pt = (ANN_unit_header_t *) (buf + offset);
      s = format (s, "%UUNIT[%d] flag %02x unit_len %d strategy_num %d\n",
		  format_white_space, now_indent, i + 1, unit_pt->flag,
		  unit_pt->unit_len, unit_pt->strategy_num);
      offset += sizeof (ANN_unit_header_t);

      // show sid/nid or not
      if (CHECK_ANN_UNIT_FLAG_N (unit_pt->flag))
	{
	  s =
	    format (s, "%Un_sid %U\n", format_white_space, now_indent,
		    format_fixedlength_string, buf + offset, COLOR_N_SID_LEN);
	  offset += COLOR_N_SID_LEN;
	}
      if (CHECK_ANN_UNIT_FLAG_L (unit_pt->flag))
	{
	  s =
	    format (s, "%Ul_sid %U\n", format_white_space, now_indent,
		    format_fixedlength_string, buf + offset, COLOR_L_SID_LEN);
	  offset += COLOR_L_SID_LEN;
	}
      if (CHECK_ANN_UNIT_FLAG_I (unit_pt->flag))
	{
	  s = format (s, "%U  nid %U\n", format_white_space, now_indent,
		      format_fixedlength_string, buf + offset, COLOR_NID_LEN);
	  offset += COLOR_NID_LEN;
	}

      now_indent += 2;
      // show strategies in unit
      for (j = 0; j < unit_pt->strategy_num; j++)
	{
	  s_len = *(u8 *) (buf + offset + 1);
	  s = format (s, "%Ustrategy_unit[%d] tag %d,len %d,value %U\n",
		      format_white_space, now_indent, j + 1,
		      *(u8 *) (buf + offset), s_len, format_fixedlength_string,
		      buf + offset + 2, s_len);
	  offset += 2 + s_len;
	}
    }

  // show px
  s = format (s, "%Upid list ", format_white_space, indent);
  for (i = 0; i < px_num; i++)
    {
      s = format (s, "[%d]%04x0000 ", i + 1, *(u16 *) (buf + offset + i * 2));
    }
  return s;
}

always_inline u8 *
format_color_get (u8 *s, va_list *args)
{
  u8 *buf = va_arg (*args, u8 *);
  if (!buf)
    return s;

  GET_header_t *get_pt = (GET_header_t *) buf;

  u32 indent = format_get_indent (s);
  s = format (s,
	      "color GET packet\n%Upacket_length %d,MTU %d,PID_num %d,"
	      "flags %02x,Minimal_PID_CP %d\n",
	      format_white_space, indent, get_pt->pkt_len, get_pt->MTU,
	      get_pt->PID_num, get_pt->flag, get_pt->Minimal_PID_CP);

  indent += 2;
  s = format (s, "%Un_sid %U\n", format_white_space, indent,
	      format_fixedlength_string, get_pt->N_sid, COLOR_N_SID_LEN);
  s = format (s, "%Ul_sid %U\n", format_white_space, indent,
	      format_fixedlength_string, get_pt->L_sid, COLOR_L_SID_LEN);
  s = format (s, "%U  nid %U\n", format_white_space, indent,
	      format_fixedlength_string, get_pt->nid, COLOR_NID_LEN);

  s = format (s, "%Upid list ", format_white_space, indent);
  int i;
  for (i = 0; i < get_pt->PID_num; i++)
    {
      u32 *p = (u32 *) (buf + sizeof (GET_header_t) + i * 4);
      s = format (s, "[%d]%08x ", i + 1, *p);
    }

  return s;
}

always_inline u8 *
format_color_data (u8 *s, va_list *args)
{
  u8 *buf = va_arg (*args, u8 *);
  if (!buf)
    return s;

  DATA_header_t *data_pt = (DATA_header_t *) buf;

  u32 indent = format_get_indent (s);
  s =
    format (s,
	    "color DATA packet\n%Upacket_length %d,header_length "
	    "%d,pid_pointer %d,pid_num %d,flags %02x\n",
	    format_white_space, indent, data_pt->pkt_len, data_pt->header_len,
	    data_pt->PID_pt, data_pt->PID_num, data_pt->flag);

  indent += 2;
  s = format (s, "%Un_sid %U\n", format_white_space, indent,
	      format_fixedlength_string, data_pt->N_sid, COLOR_N_SID_LEN);
  s = format (s, "%Ul_sid %U\n", format_white_space, indent,
	      format_fixedlength_string, data_pt->L_sid, COLOR_L_SID_LEN);
  s = format (s, "%Unid_consumer %U\n", format_white_space, indent,
	      format_fixedlength_string, data_pt->nid, COLOR_NID_LEN);

  int offset = COLOR_NID_LEN;
  if (COLOR_DATA_FLAG_R (data_pt->flag) || !COLOR_DATA_FLAG_B (data_pt->flag))
    {
      s = format (s, "%Unid_provider %U\n", format_white_space, indent,
		  format_fixedlength_string, data_pt->nid + offset,
		  COLOR_NID_LEN);
      offset += COLOR_NID_LEN;
    }

  u8 have_indent = 0;
  if (COLOR_DATA_FLAG_Q (data_pt->flag))
    {
      if (!have_indent)
	s = format (s, "%U", format_white_space, indent), have_indent = 1;
      int qos_len = *(data_pt->nid + offset);
      s = format (s, "qos_len %d,qos %U", qos_len, format_fixedlength_string,
		  data_pt->nid + offset + 1, qos_len / 8);
      offset += 1 + qos_len / 8; // qos_len is in bits
    }
  if (COLOR_DATA_FLAG_C (data_pt->flag))
    {
      if (!have_indent)
	s = format (s, "%U", format_white_space, indent), have_indent = 1;
      else
	s = format (s, ",");
      s = format (s, "hmac %08X", *(u32 *) (data_pt->nid + offset));
      offset += 4;
    }
  if (COLOR_DATA_FLAG_S (data_pt->flag))
    {
      if (!have_indent)
	s = format (s, "%U", format_white_space, indent), have_indent = 1;
      else
	s = format (s, ",");
      s = format (s, "segment_id %08X", *(u32 *) (data_pt->nid + offset));
      offset += 4;
    }
  if (have_indent)
    s = format (s, "\n");
  s = format (s, "%Upid list ", format_white_space, indent);
  for (int i = 0; i < data_pt->PID_num; i++)
    {
      s = format (s, "[%d]%08X ", i + 1, *(u32 *) (data_pt->nid + offset));
      offset += 4;
    }
  if (COLOR_DATA_FLAG_R (data_pt->flag))
    {
      s = format (s, "[reserved] %08X ", *(u32 *) (data_pt->nid + offset));
      offset += COLOR_NID_LEN;
    }
  return s;
}

always_inline u8 *
format_color_control (u8 *s, va_list *args)
{
  u8 *buf = va_arg (*args, u8 *);
  if (!buf)
    return s;

  CONTROL_header_t *control_pt = (CONTROL_header_t *) buf;

  u32 indent = format_get_indent (s);
  s =
    format (s,
	    "color CTL packet\n%Uttl %d,checksum %04x,header_length %d,tag "
	    "%d,data_length %d\n",
	    format_white_space, indent, control_pt->ttl, control_pt->checksum,
	    control_pt->header_len, control_pt->tag, control_pt->len);

  indent += 2;
  if (control_pt->tag == 5)
    {
      s = format (s, "%Uproxy register", format_white_space, indent);
    }
  else if (control_pt->tag == 6)
    {
      s = format (s, "%Uproxy register ack and return other proxy config",
		  format_white_space, indent);
    }
  else if (control_pt->tag == 7)
    {
      s = format (s, "%Ureturn config ack", format_white_space, indent);
    }
  else if (control_pt->tag == 8)
    {
      s = format (s, "%Usynchronize other proxy config", format_white_space,
		  indent);
    }
  else if (control_pt->tag == 9)
    {
      s = format (s, "%Usynchronize config ack", format_white_space, indent);
    }
  else if (control_pt->tag == 17)
    {
      s = format (s, "%Uoutbound data warning", format_white_space, indent);
    }
  else if (control_pt->tag == 18)
    {
      s = format (s, "%Uattack warning", format_white_space, indent);
    }

  return s;
}

u8 *
format_color_packet (u8 *s, va_list *args)
{
  u8 *buf = va_arg (*args, u8 *);
  switch (color_get_pkt_type (buf))
    {
    case COLOR_ANN_TYPE:
      s = format (s, "%U", format_color_ann, buf);
      break;
    case COLOR_GET_TYPE:
      s = format (s, "%U", format_color_get, buf);
      break;
    case COLOR_DATA_TYPE:
      s = format (s, "%U", format_color_data, buf);
      break;
    case COLOR_CONTROL_TYPE:
      s = format (s, "%U", format_color_control, buf);
      break;
    }
  return s;
}
