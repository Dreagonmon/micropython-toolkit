#ifndef MICROPY_PY_FRAMEBUF
#define MICROPY_PY_FRAMEBUF (1)
#endif
#include "py/dynruntime.h"
#include "font_query.h"

#ifndef FONT_DRAW_H
#define FONT_DRAW_H

typedef struct {
    mp_obj_base_t base; // object base
    mp_obj_FontQuery_t *font_query;
} mp_obj_FontDraw_t;

typedef struct {
    mp_obj_t framebuffer_obj;
    mp_obj_t framebuffer_pixel_fun;
    // mp_int_t width;
    // mp_int_t height;
} fake_framebuf_t;
// function
mp_obj_type_t *getTypeFontDraw();

#endif