import math
import time
import png      # pypng

from typing import Generator, Any

# Config
COLOR_BITDEPTH = 2      # how many bits to use for color 
                        # (make sure this is enough to fit below list!)
COLORS = {
    0: (0, 0, 0),       # black
    1: (255, 255, 255), # white
    2: (255, 0, 0),     # red
    3: (0, 0, 255),     # blue
}
TRANSPARENT = 1         # color that transparent maps to

# Constants
RADIX = "HEX"
PREAMBLE = f"""WIDTH={COLOR_BITDEPTH};
DEPTH={{}};
ADDRESS_RADIX={RADIX};
DATA_RADIX={RADIX};

CONTENT BEGIN

"""
POSTAMBLE = """
END;"""

# Helpers
def round_up_power_of_2(x: int) -> int:
    return 1 << ( int(math.log2(x)) + 1 )

def generate_data_line(addr: int, max_addr: int, data: int) -> str:
    if data.bit_length() > COLOR_BITDEPTH:
        raise ValueError(f"Bitdepth of passed data ({data.bit_depth()}) exceeds specified ({COLOR_BITDEPTH})")
    
    return f"{hex(addr)[2:].zfill((max_addr.bit_length() // 4)+1)} : {hex(data)[2:]}"

def rgb_euclidean_distance(x: tuple[int], y: tuple[int]) -> float:
    return math.sqrt((x[0] - y[0])**2 + (x[1] - y[1])**2 + (x[2] - y[2])**2)

def closest_color(in_rgb: tuple[int]) -> int:
    # <output color>: <euclidean distance>
    distances: dict[int, float] = {out_color: rgb_euclidean_distance(in_rgb, out_rgb) for out_color, out_rgb in COLORS.items()}
    return min(distances, key=distances.get)

def load_png(filename: str) -> tuple[int, int, Generator[list[tuple[int]], Any, None]]:
    reader = png.Reader(filename)
    width, height, pixels, _ = reader.asRGBA()
    return (width, height, pixels)
    
def convert_pixels(pixels: Generator[bytearray, Any, None]) -> Generator[tuple[int], Any, None]:
    # RGBA bytearray -> palette
    for row in pixels:
        i = 0
        while (i + 3) < len(row):
            yield TRANSPARENT if row[i+3] <= 127 else closest_color((row[i], row[i+1], row[i+2]))
            i += 4

# Entrypoint
def main():
    in_filename = input("Filename (.png only): ")
    width, height, pixels_raw = load_png(in_filename)

    print(f"-\nLoaded image of {width} x {height} = {width * height} pixels")

    out_filename = f"out_{int(time.time())}.mif"
    with open(out_filename, "w") as fp:
        max_addr = round_up_power_of_2(width * height) - 1

        fp.write(PREAMBLE.format(max_addr + 1))

        addr = 0
        for pixel in convert_pixels(pixels_raw):
            fp.write(generate_data_line(addr, max_addr, pixel) + '\n')
            addr += 1

        print(f"Wrote {addr} pixels to {out_filename}")
        
        for i in range(addr, max_addr + 1):
            fp.write(generate_data_line(i, max_addr, 0) + '\n')

        fp.write(POSTAMBLE)

        end_hex_addr = hex(addr)
        print(f"Finished writing to {out_filename}, address range: 0x{'0'.zfill(len(end_hex_addr)-2)} - {end_hex_addr}, padded to {hex(max_addr)}")

if __name__ == "__main__":
    main()
