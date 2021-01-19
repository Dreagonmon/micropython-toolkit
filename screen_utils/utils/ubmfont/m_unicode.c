/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2013, 2014 Damien P. George
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include "m_unicode.h"
#define UTF8_IS_NONASCII(ch) ((ch) & 0x80)
#define UTF8_IS_CONT(ch) (((ch) & 0xC0) == 0x80)

uint32_t _utf8_get_char(const byte *s) {
    uint32_t ord = *s++;
    if (!UTF8_IS_NONASCII(ord)) {
        return ord;
    }
    ord &= 0x7F;
    for (uint32_t mask = 0x40; ord & mask; mask >>= 1) {
        ord &= ~mask;
    }
    while (UTF8_IS_CONT(*s)) {
        ord = (ord << 6) | (*s++ & 0x3F);
    }
    return ord;
}

const byte *_utf8_next_char(const byte *s) {
    ++s;
    while (UTF8_IS_CONT(*s)) {
        ++s;
    }
    return s;
}

mp_uint_t _utf8_ptr_to_index(const byte *s, const byte *ptr) {
    mp_uint_t i = 0;
    while (ptr > s) {
        if (!UTF8_IS_CONT(*--ptr)) {
            i++;
        }
    }

    return i;
}

size_t _utf8_charlen(const byte *str, size_t len) {
    size_t charlen = 0;
    for (const byte *top = str + len; str < top; ++str) {
        if (!UTF8_IS_CONT(*str)) {
            ++charlen;
        }
    }
    return charlen;
}

uint8_t _utf8_check(const byte *p, size_t len) {
    uint8_t need = 0;
    const byte *end = p + len;
    for (; p < end; p++) {
        byte c = *p;
        if (need) {
            if (UTF8_IS_CONT(c)) {
                need--;
            } else {
                // mismatch
                return 0;
            }
        } else {
            if (c >= 0xc0) {
                if (c >= 0xf8) {
                    // mismatch
                    return 0;
                }
                need = (0xe5 >> ((c >> 3) & 0x6)) & 3;
            } else if (c >= 0x80) {
                // mismatch
                return 0;
            }
        }
    }
    return need == 0; // no pending fragments allowed
}
