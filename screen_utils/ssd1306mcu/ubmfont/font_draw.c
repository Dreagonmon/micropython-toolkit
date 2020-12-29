#include "font_draw.h"
#include "m_utils.h"
STATIC mp_obj_type_t mp_type_framebuf;
#include "m_unicode.h"
#define TAB_SIZE (4u)
#define ASCII_T (9u)
#define ASCII_N (10u)
#define ASCII_R (13u)
mp_obj_type_t mp_type_FontDraw;

fake_framebuf_t *initFakeFrameBuffer(mp_obj_t frame, fake_framebuf_t *dest) {
    dest->framebuffer_obj = frame;
    dest->framebuffer_pixel_fun = mp_load_attr(frame, MP_QSTR_pixel);
    // mp_printf(MICROPY_DEBUG_PRINTER, "pixel method: %d\n", dest->framebuffer_pixel_fun);
    return dest;
}
void _fake_framebuf_setpixel(fake_framebuf_t *fake_frame, mp_int_t x, mp_int_t y, mp_int_t col) {
    // mp_printf(MICROPY_DEBUG_PRINTER, "setpixel: %d %d %d\n", x, y, col);
    mp_obj_t args[] = {
        mp_obj_new_int(x),
        mp_obj_new_int(y),
        mp_obj_new_int(col),
    };
    mp_call_function_n_kw(fake_frame->framebuffer_pixel_fun, 3, 0, args);
}

// function
mp_obj_FontDraw_t *_FontDraw_make_new(mp_obj_t stream){
    mp_get_stream_raise(stream, MP_STREAM_OP_READ | MP_STREAM_OP_IOCTL);
    mp_obj_FontDraw_t *self = m_new_obj(mp_obj_FontDraw_t);
    self->base.type = (mp_obj_type_t*) &mp_type_FontDraw;
    self->font_query = _FontQuery_make_new(stream);
    return self;
}
mp_obj_t FontDraw_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    // Make sure we got a stream object
    mp_arg_check_num(n_args, n_kw, 1, 1, false);
    return MP_OBJ_FROM_PTR(_FontDraw_make_new(args[0]));
}

mp_obj_t FontDraw_get_font_size(mp_obj_t self_in) {
    mp_obj_FontDraw_t *self = MP_OBJ_TO_PTR(self_in);
    const mp_obj_t size[2] = {
        mp_obj_new_int_from_uint(self->font_query->f_width),
        mp_obj_new_int_from_uint(self->font_query->f_height)
    };
    return mp_obj_new_tuple(2, (void*)size);
}
MP_DEFINE_CONST_FUN_OBJ_1(FontDraw_get_font_size_obj, FontDraw_get_font_size);

void _draw_unicode_on_frame(mp_obj_FontQuery_t *fq, fake_framebuf_t *frame, uint32_t unicode, mp_int_t x, mp_int_t y, mp_int_t col) {
    byte *font_data_dest = m_malloc(sizeof(byte) * fq->font_data_size);
    byte *font_data = _FontQuery_query(fq, unicode, font_data_dest);
    byte *end = font_data + fq->font_data_size;
    if (font_data != NULL){
        mp_uint_t xp = x;
        mp_uint_t yp = y;
        while (font_data < end) {
            byte hdata = *font_data++;
            // mp_printf(MICROPY_DEBUG_PRINTER, "hdata: %X\n", hdata);
            for (mp_uint_t bit = 0; bit < 8; bit++) {
                byte pat = 0b10000000 >> bit;
                if (hdata & pat) {
                    // only draw if pixel set
                    if (0 <= xp && 0 <= yp) {
                        _fake_framebuf_setpixel(frame, xp, yp, col);
                    }
                }
                xp++;
            }
            if ((xp - x) >= fq->f_width) {
                xp = x;
                yp += 1;
            }
        }
    }
    m_free(font_data_dest);
}
mp_uint_t _FontDraw_draw_on_frame(mp_obj_FontQuery_t *fq, const byte *data, size_t data_len, fake_framebuf_t *frame, mp_int_t x, mp_int_t y, mp_int_t color, mp_int_t width_limit, mp_int_t height_limit) {
    mp_int_t moved_x = x;
    mp_int_t moved_y = y;
    const byte *char_point = data;
    const byte *end = data + data_len;
    mp_uint_t count = 0;
    while (char_point < end) {
        uint32_t char_unicode = _utf8_get_char(char_point);
        char_point = _utf8_next_char(char_point);
        count++;
        if (char_unicode == ASCII_T) {
            mp_int_t char_count = (moved_x - x) / fq->f_width;
            uint8_t lack_of_char = (TAB_SIZE - (char_count % TAB_SIZE)) % TAB_SIZE;
            moved_x += fq->f_width * lack_of_char;
        } else if (char_unicode == ASCII_R) {
            moved_x = x;
        } else if ((char_unicode == ASCII_N) || ((width_limit > 0) && (moved_x + fq->f_width - x > width_limit))) {
            moved_y += fq->f_height;
            moved_x = x;
        }
        if ((height_limit > 0) && (moved_y + fq->f_height - y > height_limit)) {
            return count;
        }
        if (char_unicode == ASCII_T || char_unicode == ASCII_R || char_unicode == ASCII_N) {
            continue;
        }
        // mp_printf(MICROPY_DEBUG_PRINTER, "draw: %d %d %d %d\n", char_unicode, moved_x, moved_y, color);
        _draw_unicode_on_frame(fq, frame, char_unicode, moved_x, moved_y, color);
        moved_x += fq->f_width;
    }
    return count;
}
mp_obj_t FontDraw_draw_on_frame(size_t n_args, const mp_obj_t *args){
    mp_obj_FontDraw_t *self = MP_OBJ_TO_PTR(args[0]);
    size_t text_data_len;
    byte *text_data = mp_obj_str_get_data(args[1], &text_data_len);
    // mp_printf(MICROPY_DEBUG_PRINTER, "str_len: %ld\n", text_data_len);
    // size_t text_len = _utf8_charlen(text_data, text_data_len);
    // mp_printf(MICROPY_DEBUG_PRINTER, "str_len: %ld\n", text_len);
    fake_framebuf_t frame;
    initFakeFrameBuffer(args[2], &frame);
    // mp_obj_framebuf_t *frame = MP_OBJ_TO_PTR(args[2]);
    mp_int_t x = mp_obj_get_int(args[3]);
    mp_int_t y = mp_obj_get_int(args[4]);
    mp_int_t color = 1;
    mp_int_t width_limit = -1;
    mp_int_t height_limit = -1;
    if (n_args >= 6)
        width_limit = mp_obj_get_int(args[5]);
    if (n_args >= 7)
        width_limit = mp_obj_get_int(args[6]);
    if (n_args >= 8)
        height_limit = mp_obj_get_int(args[7]);
    // draw_on_frame(self, text, frame, x, y, color=1, width_limit=-1, height_limit=-1)
    mp_uint_t count = _FontDraw_draw_on_frame(self->font_query, text_data, text_data_len, &frame, x, y, color, width_limit, height_limit);
    return mp_obj_new_int_from_uint(count);
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(FontDraw_draw_on_frame_obj, 5, 8, FontDraw_draw_on_frame);

mp_map_elem_t FontDraw_locals_dict_table[23];
MP_DEFINE_CONST_DICT(FontDraw_locals_dict_dict, FontDraw_locals_dict_table);
mp_obj_type_t *getTypeFontDraw(){
    mp_type_FontDraw.base.type = (void*)&mp_type_type;
    mp_type_FontDraw.name = MP_QSTR_FontDraw;
    mp_type_FontDraw.make_new = FontDraw_make_new;
    FontDraw_locals_dict_table[0] = (mp_map_elem_t){ MP_OBJ_NEW_QSTR(MP_QSTR_get_font_size), MP_OBJ_FROM_PTR(&FontDraw_get_font_size_obj) };
    FontDraw_locals_dict_table[1] = (mp_map_elem_t){ MP_OBJ_NEW_QSTR(MP_QSTR_draw_on_frame), MP_OBJ_FROM_PTR(&FontDraw_draw_on_frame_obj) };
    mp_type_FontDraw.locals_dict = (void*)&FontDraw_locals_dict_dict;
    return &mp_type_FontDraw;
}