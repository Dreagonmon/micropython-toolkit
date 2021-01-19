#include "py/dynruntime.h"
#ifndef M_UTILS_H
#define M_UTILS_H (1)
#if !defined(__linux__)
void *memcpy(void *dst, const void *src, size_t n);
void *memset(void *s, int c, size_t n);
#endif
void *memmove(void *dest, const void *src, size_t n);
void *malloc(size_t n);
void *realloc(void *ptr, size_t n);
void *calloc(size_t n, size_t m);
void free(void *ptr);
void abort_(void);
// FUNCTION
mp_uint_t _readinto(mp_obj_t stream, byte *buf, mp_uint_t len, int *errcode);
mp_off_t _seek(mp_obj_t stream, mp_off_t offset, int *errcode);
uint32_t bytes_to_uint(byte *byts, uint8_t len);
uint8_t uint_to_bytes(uint32_t v, byte *byts, uint8_t len);
int32_t binary_search_bytes(byte *lis, byte *target, uint32_t llen, uint8_t target_pos, uint8_t block_size);
#endif