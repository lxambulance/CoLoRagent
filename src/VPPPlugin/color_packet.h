#ifndef _RTE_COLOR_H_
#define _RTE_COLOR_H_

#include <vppinfra/string.h>
#include <vppinfra/types.h>
#include <vppinfra/clib.h>
#include <vppinfra/format.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// version
#define COLOR_PROTOCOL 0x7

// package
#define COLOR_ANN_TYPE	   0x1
#define COLOR_GET_TYPE	   0x2
#define COLOR_DATA_TYPE	   0x3
#define COLOR_CONTROL_TYPE 0x4

// length of optional fields (byte)
#define COLOR_SK_LEN  4
#define COLOR_PX_LEN  2
#define COLOR_PID_LEN 4

#define COLOR_N_SID_LEN 16
#define COLOR_L_SID_LEN 20
#define COLOR_SID_LEN	(COLOR_N_SID_LEN + COLOR_L_SID_LEN)
#define COLOR_NID_LEN	16

#define COLOR_PUBLICKEY_FRONT_LEN 2
#define COLOR_QOS_FRONT_LEN	  1
#define COLOR_SEG_ID_LEN	  4
#define COLOR_HMAC_LEN		  4
#define COLOR_MINIMAL_PID_CP_LEN  2

// flag F
#define COLOR_FLAG_F(flag)	    ((flag) &0x80)
#define COLOR_REV_FLAG_F(flag)	    ((flag) ^ 0x80)
#define COLOR_DATA_SET_FLAG_F(flag) ((flag) | 0x80)

// flag of GET packet
#define COLOR_GET_FLAG_F(flag)	   COLOR_FLAG_F (flag)
#define COLOR_GET_REV_FLAG_F(flag) COLOR_REV_FLAG_F (flag)
#define COLOR_GET_FLAG_K(flag)	   ((flag) &0x40)
#define COLOR_GET_FLAG_Q(flag)	   ((flag) &0x20)
#define COLOR_GET_FLAG_S(flag)	   ((flag) &0x10)
#define COLOR_GET_FLAG_A(flag)	   ((flag) &0x08)

// flag of DATA packet
#define COLOR_DATA_FLAG_F(flag)	    COLOR_FLAG_F (flag)
#define COLOR_DATA_REV_FLAG_F(flag) COLOR_REV_FLAG_F (flag)
#define COLOR_DATA_FLAG_B(flag)	    ((flag) &0x40)
#define COLOR_DATA_FLAG_R(flag)	    ((flag) &0x20)
#define COLOR_DATA_FLAG_M(flag)	    ((flag) &0x10)
#define COLOR_DATA_FLAG_Q(flag)	    ((flag) &0x08)
#define COLOR_DATA_FLAG_C(flag)	    ((flag) &0x04)
#define COLOR_DATA_FLAG_S(flag)	    ((flag) &0x02)

// flag of ANN packet
#define COLOR_ANN_FLAG_F(flag)	   COLOR_FLAG_F (flag)
#define COLOR_ANN_REV_FLAG_F(flag) COLOR_REV_FLAG_F (flag)
#define COLOR_ANN_FLAG_K(flag)	   ((flag) &0x40)
#define COLOR_ANN_FLAG_P(flag)	   ((flag) &0x20)

#define COLOR_ANN_FLAG_N(flag) ((flag) &0x80)
#define COLOR_ANN_FLAG_L(flag) ((flag) &0x40)
#define COLOR_ANN_FLAG_I(flag) ((flag) &0x20)

/* ------------------------------Package format of
 * ANN---------------------------------- */
// ANN = header + ANN_unit[unit_num] + (publickey) + (AS_PATH) + PX[px_num]
// flag = F/K/P
struct ANN_header
{
  u8 version_package;
  u8 ttl;
  u16 pkt_len;
  u16 checksum;
  u8 flag;
  u8 unit_px_num;
} __attribute__ ((__packed__));
typedef struct ANN_header ANN_header_t;

// ANN_unit = header + (N_sid) + (L_sid) + (nid) +
// ANN_strategy_unit[strategy_num]
struct ANN_unit_header
{
  u8 flag;
  u8 unit_len;
  u8 strategy_num;
} __attribute__ ((__packed__));
typedef struct ANN_unit_header ANN_unit_header_t;

// ANN_strategy_unit = header + value[length]
struct ANN_strategy_header
{
  u8 tag;
  u8 len;
} __attribute__ ((__packed__));
typedef struct ANN_strategy_header ANN_strategy_header_t;

/* ------------------------------Package format of
 * GET---------------------------------- */
// GET = header + (publickey) + (QoS) + (Seg_ID) + PID[PID_num] + (PID_RES)
// flag = F/K/Q/S/A
struct GET_header
{
  u8 version_package;
  u8 ttl;
  u16 pkt_len;
  u16 checksum;
  u16 MTU;
  u8 PID_num;
  u8 flag;
  u16 Minimal_PID_CP;
  u8 N_sid[16];
  u8 L_sid[20];
  u8 nid[16];
} __attribute__ ((__packed__));
typedef struct GET_header GET_header_t;

/* ------------------------------Package format of
 * DATA---------------------------------- */
// DATA = header + (QoS) + (HMAC) + (Seg_ID) + (Minimal_PID_CP) + PID[PID_num]
// flag = F/B/R/M/Q/C/S
struct DATA_header
{
  u8 version_package;
  u8 ttl;
  u16 pkt_len;
  u16 checksum;
  u8 header_len;
  u8 PID_pt;
  u8 PID_num;
  u8 flag;
  u8 N_sid[16];
  u8 L_sid[20];
  u8 nid[16];
} __attribute__ ((__packed__));
typedef struct DATA_header DATA_header_t;

struct CONTROL_header
{
  u8 version_package;
  u8 ttl;
  u16 checksum;
  u8 header_len;
  u8 tag;
  u16 len;
} __attribute__ ((__packed__));
typedef struct CONTROL_header CONTROL_header_t;

/* ------------------------------Function of
 * color---------------------------------- */

#define DEFAULT_TTL 64

#define GET_PROTOCOL_TYPE(x) (((x) &0xf0) >> 4)
#define GET_PACKAGE_TYPE(x)  ((x) &0x0f)

#define GET_ANN_UNIT_NUM(x) ((x) >> 4)
#define ADD_ANN_UNIT_NUM(x) ((x) = (x) + 0x10)
#define GET_ANN_PX_NUM(x)   ((x) &0x0f)
#define ADD_ANN_PX_NUM(x)   ((x) = (x) + 0x01)

#define CHECK_ANN_UNIT_FLAG_N(flag) (((flag) &0x80) == 0x80)
#define CHECK_ANN_UNIT_FLAG_L(flag) (((flag) &0x40) == 0x40)
#define CHECK_ANN_UNIT_FLAG_I(flag) (((flag) &0x20) == 0x20)
#define GET_ANN_UNIT_FLAG_AM(flag)  (((flag) << 3) >> 6)
#define SET_ANN_UNIT_FLAG_N(flag)   ((flag) = ((flag) | 0x80))
#define SET_ANN_UNIT_FLAG_L(flag)   ((flag) = ((flag) | 0x40))
#define SET_ANN_UNIT_FLAG_I(flag)   ((flag) = ((flag) | 0x20))

#define CHECK_FLAG_F(flag)   (((flag) &0x80) == 0x80)
#define REVERSE_FLAG_F(flag) ((flag) = ((flag) ^ 0x80))

// stage 1 & 2
#define CONTROL_TAG_SYN_RM_CONFIG	1
#define ACK_CONTROL_TAG_SYN_RM_CONFIG	2
#define CONTROL_TAG_SYN_BR_CONFIG	3
#define ACK_CONTROL_TAG_SYN_BR_CONFIG	4
#define CONTROL_TAG_SYN_RM_STRATEGY	10
#define ACK_CONTROL_TAG_SYN_RM_STRATEGY 11
// stage 3
#define CONTROL_TAG_REG_PROXY		    5
#define CONTROL_TAG_RET_PROXY_CONFIG	    6
#define CONTROL_TAG_ACK_PROXY_CONFIG	    7
#define CONTROL_TAG_SYN_BR_PROXY_CONFIG	    8
#define ACK_CONTROL_TAG_SYN_BR_PROXY_CONFIG 9
// attack warning
#define CONTROL_TAG_ODC		   16
#define CONTROL_TAG_ODC_WARNING	   17
#define CONTROL_TAG_ATTACK_WARNING 18

int ANN_check_checksum (u8 *buf);
void ANN_update_checksum (u8 *buf);
int GET_check_checksum (u8 *buf);
void GET_update_checksum (u8 *buf);
int DATA_check_checksum (u8 *buf);
void DATA_update_checksum (u8 *buf);
int CONTROL_check_checksum (u8 *buf);
void CONTROL_update_checksum (u8 *buf);

void ANN_init (u8 *buf);
void GET_init (u8 *buf, u8 *n_sid, u8 *l_sid, u8 *nid);
void DATA_init (u8 *buf, u8 *n_sid, u8 *l_sid, u8 *nid);
void CONTROL_init (u8 *buf, u8 tag, u16 len, u8 *con_data);

void ANN_append_unit (u8 *buf, u8 *unit);
void ANN_unit_construct (u8 *ubuf, u8 *n_sid, u8 *l_sid, u8 *nid);
void ANN_unit_append_strategy (u8 *ubuf, u8 t, u8 l, u8 *v);
void ANN_append_px (u8 *buf, u16 px);
int ANN_get_pkt_length (u8 *buf);
void GET_append_pid (u8 *buf, u32 pid);
u32 GET_calculate_PID (u8 *pkt, u32 sk, u16 to_px);
void DATA_append_pid (u8 *buf, u32 pid);
void DATA_append_data (u8 *buf, u8 *data, int len);
int color_get_pkt_protocol (u8 *buf);
int color_get_pkt_type (u8 *buf);
int color_get_pkt_length (u8 *buf);

u8 *format_color_packet (u8 *s, va_list *args);

always_inline u16
calculate_checksum (u16 *buf, u16 count)
{
  u32 sum = 0;
  while (count > 1)
    {
      sum += *buf++;
      count -= 2;
    }
  if (count > 0)
    sum += *(u8 *) buf;
  sum = (sum >> 16) + (sum & 0xffff);
  sum += (sum >> 16);
  return (u16) (~sum);
}

#endif /*_RTE_COLOR_H_*/
