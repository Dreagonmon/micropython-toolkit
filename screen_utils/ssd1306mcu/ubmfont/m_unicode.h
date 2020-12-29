#include <stddef.h>
#include <stdint.h>
typedef unsigned char byte;
typedef unsigned int mp_uint_t;
#ifndef UNICODE_H
#define UNICODE_H
uint32_t _utf8_get_char(const byte *s);
const byte *_utf8_next_char(const byte *s);
mp_uint_t _utf8_ptr_to_index(const byte *s, const byte *ptr);
size_t _utf8_charlen(const byte *str, size_t len);
uint8_t _utf8_check(const byte *p, size_t len);
#endif