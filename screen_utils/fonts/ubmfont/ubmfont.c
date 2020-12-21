/* see modio.c, for example, call python function from C
*/

// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"

typedef struct {
    mp_obj_base_t base; // object base
    mp_obj_t stream;
    uint8_t f_width, f_height, max_u8_size;
    uint16_t font_data_size;
} mp_obj_FontQuery_t;

byte read1(mp_obj_t stream, int *errcode){
    const mp_obj_base_t* o = MP_OBJ_TO_PTR(stream);
    const mp_stream_p_t *stream_p = o->type->protocol;
    byte buf1[1];
    stream_p->read(MP_OBJ_FROM_PTR(stream), buf1, 1, errcode);
    return buf1[0];
}
mp_uint_t readinto(mp_obj_t stream, byte *buf, mp_uint_t len, int *errcode){
    const mp_obj_base_t* o = MP_OBJ_TO_PTR(stream);
    const mp_stream_p_t *stream_p = o->type->protocol;
    return stream_p->read(MP_OBJ_FROM_PTR(stream), buf, len, errcode);
}
mp_off_t seek(mp_obj_t stream, mp_off_t offset, int *errcode) {
    const mp_obj_base_t* o = MP_OBJ_TO_PTR(stream);
    const mp_stream_p_t *stream_p = o->type->protocol;
    struct mp_stream_seek_t seek_s;
    seek_s.offset = offset;
    seek_s.whence = MP_SEEK_SET;
    stream_p->ioctl(MP_OBJ_FROM_PTR(stream), MP_STREAM_SEEK, (mp_uint_t)(uintptr_t)&seek_s, errcode);
    return seek_s.offset;
}
uint32_t bytes_to_uint(byte *byts, uint8_t len) {
    uint32_t v = 0;
    uint8_t p = 0;
    while (p < len)
    {
        v <<= 8;
        v |= byts[p] & 0xFF;
        p ++;
    }
    return v;
}
uint8_t uint_to_bytes(uint32_t v, byte *byts, uint8_t len) {
    uint8_t p = 0;
    while (p < len)
    {
        byts[p] = (byte)((v >> (len - p - 1)*8) & 0xFF);
        p ++;
    }
    return p;
}
int32_t binary_search_bytes(byte *lis, byte *target, uint32_t llen, uint8_t target_pos, uint8_t block_size){
    // uint8_t debug = 0;
    // if (llen >= 2 && lis[0]==0x4C && lis[1]==0x6B) debug=1;
    int32_t left = 0;
    int32_t right = llen - 1;
    while (left <= right) {
        int32_t mid = (left + right) / 2 / block_size;
        uint32_t mid_byt_offset = mid*block_size;
        // if (debug) mp_printf(MICROPY_DEBUG_PRINTER, "left: %d right: %d mid: %d\n", left, right, mid);
        int8_t eq = 0;
        for (uint8_t i = 0; i < block_size; i++) {
            byte b = lis[mid_byt_offset + i];
            byte t = target[target_pos + i];
            if (b == t) {
                continue;
            } else if (t < b) {
                eq = -1;
                break;
            } else {
                eq = 1;
                break;
            }
        }
        if (eq < 0) {
            right = mid - block_size;
        } else if (eq > 0) {
            left = mid + block_size;
        } else {
            return mid;
        }
    }
    return -1; // not found
}

STATIC mp_obj_t FontQuery_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    // Make sure we got a stream object
    mp_arg_check_num(n_args, n_kw, 1, 1, false);
    mp_get_stream_raise(args[0], MP_STREAM_OP_READ | MP_STREAM_OP_IOCTL);
    mp_obj_FontQuery_t *self = m_new_obj(mp_obj_FontQuery_t);
    self->base.type = type;
    self->stream = args[0];
    int errcode;
    byte buf[4];
    mp_uint_t rd = readinto(self->stream, buf, 4, &errcode);
    if (rd != 4 || buf[0] != (byte)'u' || rd != (mp_uint_t)4) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid file"));
        return MP_OBJ_FROM_PTR(self);
    }
    self->max_u8_size = buf[1];
    self->f_width = buf[2];
    self->f_height = buf[3];
    uint8_t w = self->f_width / 8;
    w += self->f_width % 8 == 0 ? 0 : 1;
    self->font_data_size = self->f_height * w;
    return MP_OBJ_FROM_PTR(self);
}
STATIC mp_obj_t _FontQuery_query_(mp_obj_FontQuery_t *self, byte *unicode_target_byts, uint8_t match_pos, uint32_t offset) {
    // uint8_t debug = 0;
    // if (offset == 0x36B9) debug = 1;
    mp_obj_t res = mp_const_none;
    int errcode;
    byte buf[4];
    // area header
    seek(self->stream, (mp_off_t)offset, &errcode);
    mp_uint_t rd = readinto(self->stream, buf, 4, &errcode);
    if (rd != 4){
        mp_raise_ValueError(MP_ERROR_TEXT("invalid file"));
        return res;
    }
    offset += 4;
    const uint16_t this_area_count = (uint16_t) bytes_to_uint(buf, (uint8_t)2);
    const uint8_t this_area_type = buf[2];
    const uint8_t index_match_size = buf[3];
    if (this_area_type == (uint8_t)0x00 && (index_match_size != self->max_u8_size - match_pos)){
        return res;
    }
    // prepare match options
    uint32_t matchs_index_byts_len = index_match_size * this_area_count;
    byte *matchs_index_byts = m_new(byte, matchs_index_byts_len);
    rd = readinto(self->stream, matchs_index_byts, matchs_index_byts_len, &errcode);
    if (rd != matchs_index_byts_len){
        mp_raise_ValueError(MP_ERROR_TEXT("invalid file"));
        m_free(matchs_index_byts);
        return res;
    }
    offset += matchs_index_byts_len;
    // search index
    // if (debug) mp_printf(MICROPY_DEBUG_PRINTER, "len: %d matchpose: 0x%X matchsize: %d index0: 0x%x index1: 0x%X\n", matchs_index_byts_len, match_pos, index_match_size, matchs_index_byts[0], matchs_index_byts[1]);
    int32_t index = binary_search_bytes(matchs_index_byts, unicode_target_byts, matchs_index_byts_len, match_pos, index_match_size);
    // if (debug) mp_printf(MICROPY_DEBUG_PRINTER, "count: %d matchpose: 0x%X index: %d\n", matchs_index_byts_len, match_pos, index);
    m_free(matchs_index_byts);
    // process resault
    if (index < 0) {
        return res;
    }
    if (this_area_type == 0x00) {
        uint32_t target_offset = offset + self->font_data_size * (uint32_t)index;
        byte *buffer = m_new(byte, self->font_data_size);
        seek(self->stream, target_offset, &errcode);
        rd = readinto(self->stream, buffer, self->font_data_size, &errcode);
        if (rd != self->font_data_size){
            mp_raise_ValueError(MP_ERROR_TEXT("invalid file"));
            m_free(buffer);
            return res;
        }
        res = mp_obj_new_bytearray_by_ref(self->font_data_size, buffer);
    } else {
        // next area
        uint32_t target_offset = offset + 4 * (uint32_t)index;
        seek(self->stream, target_offset, &errcode);
        rd = readinto(self->stream, buf, 4, &errcode);
        if (rd != 4){
            mp_raise_ValueError(MP_ERROR_TEXT("invalid file"));
            return res;
        }
        uint32_t jump_offset = bytes_to_uint(buf, 4);
        // if (debug) mp_printf(MICROPY_DEBUG_PRINTER, "index: %d jump: 0x%X\n", index, jump_offset);
        res = _FontQuery_query_(self, unicode_target_byts, match_pos + index_match_size, jump_offset);
    }
    return res;
}
STATIC mp_obj_t FontQuery_query(mp_obj_t self_in, mp_obj_t unicode) {
    mp_obj_FontQuery_t *self = MP_OBJ_TO_PTR(self_in);
    uint32_t unic = (uint32_t)mp_obj_get_int(unicode);
    byte *unicode_target_byts = m_new(byte, self->max_u8_size);
    // mp_printf(MICROPY_DEBUG_PRINTER, "unicode: 0x%X\n", unic);
    uint_to_bytes(unic, unicode_target_byts, self->max_u8_size);
    mp_obj_t data = _FontQuery_query_(self, unicode_target_byts, 0, 4);
    // clean up
    m_free(unicode_target_byts);
    return data;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(FontQuery_query_obj, FontQuery_query);

STATIC mp_obj_t FontQuery_get_font_size(mp_obj_t self_in) {
    mp_obj_FontQuery_t *self = MP_OBJ_TO_PTR(self_in);
    const mp_obj_t size[2] = {
        mp_obj_new_int_from_uint(self->f_width),
        mp_obj_new_int_from_uint(self->f_height)
    };
    return mp_obj_new_tuple(2, (void*)size);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(FontQuery_get_font_size_obj, FontQuery_get_font_size);

// This is the entry point and is called when the module is imported
mp_obj_type_t mp_type_FontQuery;
mp_map_elem_t FontQuery_locals_dict_table[2];
STATIC MP_DEFINE_CONST_DICT(FontQuery_locals_dict, FontQuery_locals_dict_table);
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    mp_type_FontQuery.base.type = (void*)&mp_type_type;
    mp_type_FontQuery.name = MP_QSTR_FontQuery;
    mp_type_FontQuery.make_new = FontQuery_make_new;
    FontQuery_locals_dict_table[0] = (mp_map_elem_t){ MP_OBJ_NEW_QSTR(MP_QSTR_query), MP_OBJ_FROM_PTR(&FontQuery_query_obj) };
    FontQuery_locals_dict_table[1] = (mp_map_elem_t){ MP_OBJ_NEW_QSTR(MP_QSTR_get_font_size), MP_OBJ_FROM_PTR(&FontQuery_get_font_size_obj) };
    mp_type_FontQuery.locals_dict = (void*)&FontQuery_locals_dict;

    mp_store_global(MP_QSTR_FontQuery, MP_OBJ_FROM_PTR(&mp_type_FontQuery));
    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}
