import framebuf
import sys
from usdl2 import SDL_Init, SDL_INIT_VIDEO, SDL_WINDOWPOS_CENTERED, SDL_RENDERER_SOFTWARE, SDL_WINDOW_FULLSCREEN_DESKTOP, SDL_Quit
from usdl2 import SDL_CreateWindow, SDL_CreateRenderer, SDL_RenderSetLogicalSize, SDL_RenderSetIntegerScale, SDL_DestroyWindow, SDL_DestroyRenderer
from usdl2 import SDL_SetRenderDrawColor, SDL_RenderFillRect, SDL_RenderFillRects, SDL_RenderPresent
from usdl2 import SDL_TRUE, SDL_Rect
from usdl2 import SDL_PollEvent, SDL_GetEventType
from usdl2 import SDL_EVENT_QUIT
from _thread import start_new_thread
from time import sleep

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
PIXEL_SIZE = 8
PIXEL_GAP = 1
START_SDL_EVENT_DAEMON = True

tid = -1

__event_buffer = bytearray(128)


def sdl_consume_event():
    while SDL_PollEvent(__event_buffer) == 1:
        sdl_event_type = SDL_GetEventType(__event_buffer)
        if sdl_event_type == SDL_EVENT_QUIT:
            SDL_Quit()


def __thread_poll_sdl_event():
    # type: () -> list
    while True:
        sdl_consume_event()
        sleep(0)


def _start_poll_sdl_event():
    global tid
    if tid < 0:
        tid = start_new_thread(__thread_poll_sdl_event, tuple())


class SSD1306_SDL(framebuf.FrameBuffer):
    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, pixel_scale=PIXEL_SIZE, pixel_gap=PIXEL_GAP):
        self._window = 0
        self._renderer = 0
        self._width = width
        self._height = height
        self._pixel_scale = pixel_scale
        self._pixel_gap = pixel_gap
        screen_flag = 0
        argv = sys.argv  # type: list[str]
        for opt in argv:
            if opt == "-Ofullscreen":
                screen_flag = screen_flag | SDL_WINDOW_FULLSCREEN_DESKTOP
            elif opt.startswith("-Opixelsize"):
                size = int(opt[len("-Opixelsize"):])
                if size >= 1 and size <= 16:
                    pixel_scale = size
            elif opt.startswith("-Opixelgap"):
                size = int(opt[len("-Opixelgap"):])
                if size >= 0 and size <= 4:
                    PIXEL_GAP = size
        self._screen_flag = screen_flag
        super().__init__(bytearray(width*height//8), width, height, framebuf.MONO_HLSB)
        self.init_display()

    def init_display(self):
        SDL_Init(SDL_INIT_VIDEO)
        self._window = SDL_CreateWindow(
            "SSD1306_SDL",
            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
            self._width * self._pixel_scale, self._height * self._pixel_scale,
            self._screen_flag
        )
        self._renderer = SDL_CreateRenderer(
            self._window, -1, SDL_RENDERER_SOFTWARE)
        SDL_RenderSetLogicalSize(
            self._renderer,
            self._width * self._pixel_scale,
            self._height * self._pixel_scale
        )
        SDL_RenderSetIntegerScale(self._renderer, SDL_TRUE)
        if START_SDL_EVENT_DAEMON:
            _start_poll_sdl_event()

    def poweroff(self):
        pass

    def poweron(self):
        pass

    def contrast(self, contrast):
        pass

    def invert(self, invert):
        pass

    def show(self):
        self.refresh(0, 0, self._width, self._height)

    def refresh(self, x, y, w, h):
        rects = bytearray()
        rects_count = 0
        SDL_SetRenderDrawColor(self._renderer, 0, 0, 0, 255)
        SDL_RenderFillRect(self._renderer, SDL_Rect(
            x * self._pixel_scale, y * self._pixel_scale, w * self._pixel_scale, h * self._pixel_scale))
        for iy in range(h):
            for ix in range(w):
                px = x + ix
                py = y + iy
                if self.pixel(px, py) > 0:
                    rects.extend(SDL_Rect(px * self._pixel_scale, py * self._pixel_scale,
                                 self._pixel_scale - self._pixel_gap, self._pixel_scale - self._pixel_gap))
                    rects_count += 1
        if rects_count > 0:
            SDL_SetRenderDrawColor(self._renderer, 255, 255, 255, 255)
            SDL_RenderFillRects(self._renderer, rects, rects_count)
        SDL_RenderPresent(self._renderer)

    def __del__(self):
        SDL_DestroyRenderer(self._renderer)
        self._renderer = 0
        SDL_DestroyWindow(self._window)
        self._window = 0
