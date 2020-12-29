#include "m_utils.h"

#if !defined(__linux__)
void *memcpy(void *dst, const void *src, size_t n) {
    return mp_fun_table.memmove_(dst, src, n);
}
void *memset(void *s, int c, size_t n) {
    return mp_fun_table.memset_(s, c, n);
}
#endif

void *memmove(void *dest, const void *src, size_t n) {
    return mp_fun_table.memmove_(dest, src, n);
}

void *malloc(size_t n) {
    void *ptr = m_malloc(n);
    return ptr;
}
void *realloc(void *ptr, size_t n) {
    mp_printf(&mp_plat_print, "UNDEF %d\n", __LINE__);
    return NULL;
}
void *calloc(size_t n, size_t m) {
    void *ptr = m_malloc(n * m);
    // memory already cleared by conservative GC
    return ptr;
}

void free(void *ptr) {
    m_free(ptr);
}

void abort_(void) {
    nlr_raise(mp_obj_new_exception(mp_load_global(MP_QSTR_RuntimeError)));
}

mp_uint_t _readinto(mp_obj_t stream, byte *buf, mp_uint_t len, int *errcode){
    const mp_obj_base_t* o = MP_OBJ_TO_PTR(stream);
    const mp_stream_p_t *stream_p = o->type->protocol;
    return stream_p->read(MP_OBJ_FROM_PTR(stream), buf, len, errcode);
}
mp_off_t _seek(mp_obj_t stream, mp_off_t offset, int *errcode) {
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
