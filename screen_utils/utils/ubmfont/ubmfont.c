/* see modio.c, for example, call python function from C
*/

// Include the header file to get access to the MicroPython API
#define MICROPY_PY_FRAMEBUF (1)
#include "font_query.h"
#include "font_draw.h"
#include "m_utils.h"
#include "py/dynruntime.h"

// This is the entry point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    // FontQuery
    mp_store_global(MP_QSTR_FontQuery, MP_OBJ_FROM_PTR(getTypeFontQuery()));
    mp_store_global(MP_QSTR_FontDraw, MP_OBJ_FROM_PTR(getTypeFontDraw()));

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}
