/**
 * FontQuery class
 */

#include "font_query.h"
#include "m_utils.h"
mp_obj_type_t mp_type_FontQuery;

// function
mp_obj_FontQuery_t *_FontQuery_make_new(mp_obj_t stream){
    mp_get_stream_raise(stream, MP_STREAM_OP_READ | MP_STREAM_OP_IOCTL);
    mp_obj_FontQuery_t *self = m_new_obj(mp_obj_FontQuery_t);
    self->base.type = (mp_obj_type_t*) &mp_type_FontQuery;
    self->stream = stream;
    int errcode;
    byte buf[4];
    mp_uint_t rd = _readinto(self->stream, buf, 4, &errcode);
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
    return self;
}

mp_obj_t FontQuery_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    // Make sure we got a stream object
    mp_arg_check_num(n_args, n_kw, 1, 1, false);
    return MP_OBJ_FROM_PTR(_FontQuery_make_new(args[0]));
}

byte *_FontQuery_query_loop(mp_obj_FontQuery_t *self, byte *unicode_target_byts, uint8_t match_pos, uint32_t offset, byte *dest) {
    // uint8_t debug = 0;
    // if (offset == 0x36B9) debug = 1;
    // mp_obj_t res = mp_const_none;
    void *res = NULL;
    int errcode;
    byte buf[4];
    // area header
    _seek(self->stream, (mp_off_t)offset, &errcode);
    mp_uint_t rd = _readinto(self->stream, buf, 4, &errcode);
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
    byte *matchs_index_byts = m_malloc(sizeof(byte) * matchs_index_byts_len);
    rd = _readinto(self->stream, matchs_index_byts, matchs_index_byts_len, &errcode);
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
        byte *buffer;
        if (dest == NULL) {
            buffer = m_malloc(sizeof(byte) * self->font_data_size);
        } else {
            buffer = dest;
        }
        _seek(self->stream, target_offset, &errcode);
        rd = _readinto(self->stream, buffer, self->font_data_size, &errcode);
        if (rd != self->font_data_size){
            mp_raise_ValueError(MP_ERROR_TEXT("invalid file"));
            m_free(buffer);
            return res;
        }
        // res = mp_obj_new_bytearray_by_ref(self->font_data_size, buffer);
        res = buffer;
    } else {
        // next area
        uint32_t target_offset = offset + 4 * (uint32_t)index;
        _seek(self->stream, target_offset, &errcode);
        rd = _readinto(self->stream, buf, 4, &errcode);
        if (rd != 4){
            mp_raise_ValueError(MP_ERROR_TEXT("invalid file"));
            return res;
        }
        uint32_t jump_offset = bytes_to_uint(buf, 4);
        // if (debug) mp_printf(MICROPY_DEBUG_PRINTER, "index: %d jump: 0x%X\n", index, jump_offset);
        res = _FontQuery_query_loop(self, unicode_target_byts, match_pos + index_match_size, jump_offset, dest);
    }
    return res;
}

byte *_FontQuery_query(mp_obj_FontQuery_t *self, uint32_t unicode, byte *dest) {
    byte *unicode_target_byts = m_malloc(sizeof(byte) * self->max_u8_size);
    uint_to_bytes(unicode, unicode_target_byts, self->max_u8_size);
    byte *data = _FontQuery_query_loop(self, unicode_target_byts, 0, 4, dest);
    m_free(unicode_target_byts);
    return data;
}

mp_obj_t FontQuery_query(mp_obj_t self_in, mp_obj_t unicode) {
    mp_obj_FontQuery_t *self = MP_OBJ_TO_PTR(self_in);
    uint32_t unic = (uint32_t)mp_obj_get_int(unicode);
    byte *data = _FontQuery_query(self, unic, NULL);
    // return
    if (data == NULL) {
        return mp_const_none;
    } else {
        return mp_obj_new_bytearray_by_ref(self->font_data_size, data);
    }
}
MP_DEFINE_CONST_FUN_OBJ_2(FontQuery_query_obj, FontQuery_query);

mp_obj_t FontQuery_get_font_size(mp_obj_t self_in) {
    mp_obj_FontQuery_t *self = MP_OBJ_TO_PTR(self_in);
    const mp_obj_t size[2] = {
        mp_obj_new_int_from_uint(self->f_width),
        mp_obj_new_int_from_uint(self->f_height)
    };
    return mp_obj_new_tuple(2, (void*)size);
}
MP_DEFINE_CONST_FUN_OBJ_1(FontQuery_get_font_size_obj, FontQuery_get_font_size);

// define type FontQuery
mp_map_elem_t FontQuery_locals_dict_table[2];
MP_DEFINE_CONST_DICT(FontQuery_locals_dict, FontQuery_locals_dict_table);
mp_obj_type_t *getTypeFontQuery(){
    mp_type_FontQuery.base.type = (void*)&mp_type_type;
    mp_type_FontQuery.name = MP_QSTR_FontQuery;
    mp_type_FontQuery.make_new = FontQuery_make_new;
    FontQuery_locals_dict_table[0] = (mp_map_elem_t){ MP_OBJ_NEW_QSTR(MP_QSTR_query), MP_OBJ_FROM_PTR(&FontQuery_query_obj) };
    FontQuery_locals_dict_table[1] = (mp_map_elem_t){ MP_OBJ_NEW_QSTR(MP_QSTR_get_font_size), MP_OBJ_FROM_PTR(&FontQuery_get_font_size_obj) };
    mp_type_FontQuery.locals_dict = (void*)&FontQuery_locals_dict;
    return &mp_type_FontQuery;
}
