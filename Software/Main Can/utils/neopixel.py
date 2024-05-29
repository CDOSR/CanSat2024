import machine
import neopixel
import time

class NeoPixelControl:
    def __init__(self, pin_number, num_pixels):
        self.pin = machine.Pin(pin_number, machine.Pin.OUT)
        self.num_pixels = num_pixels
        self.np = neopixel.NeoPixel(self.pin, num_pixels)
        self.clear()

    def set_pixel(self, index, r, g, b):
        """Set the color of a single pixel."""
        for i in range(self.num_pixels):
            self.np[i] = (r, g, b)
        self.np.write()

    def fill(self, color):
        """Fill all pixels with the given color."""
        for i in range(self.num_pixels):
            self.np[i] = color

    def clear(self):
        """Clear all pixels."""
        self.fill((0, 0, 0))
        self.update()

    def update(self):
        """Update the strip to show the changes."""
        self.np.write()

    def rainbow_cycle(self, wait_ms=20, iterations=1):
        """Display a rainbow cycle across all pixels."""
        import time
        for j in range(256*iterations):
            for i in range(self.num_pixels):
                pixel_index = (i * 256 // self.num_pixels) + j
                self.np[i] = self.wheel(pixel_index & 255)
            self.update()
            time.sleep_ms(wait_ms)

    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        else:
            pos -= 170
            return (pos * 3, 0, 255 - pos * 3)

# # Usage example:
# if __name__ == '__main__':
#     pixel_control = NeoPixelControl(pin_number=5, num_pixels=8)
#     pixel_control.rainbow_cycle(50, 5)
