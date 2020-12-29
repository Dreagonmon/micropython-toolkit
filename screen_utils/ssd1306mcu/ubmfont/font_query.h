/**
 * FontQuery class
 */

#include "py/dynruntime.h"

#ifndef FONT_QUERY_H
#define FONT_QUERY_H
typedef struct {
    mp_obj_base_t base; // object base
    mp_obj_t stream;
    uint8_t f_width, f_height, max_u8_size;
    uint16_t font_data_size;
} mp_obj_FontQuery_t;

// define type FontQuery
mp_obj_FontQuery_t *_FontQuery_make_new(mp_obj_t stream);
byte *_FontQuery_query(mp_obj_FontQuery_t *self, uint32_t unicode, byte *dest);
mp_obj_type_t *getTypeFontQuery();
#endif