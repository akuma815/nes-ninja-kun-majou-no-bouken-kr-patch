"""NES 2bpp planar tile codec; no palette or mapper assumptions."""
from PIL import Image
def decode_tile(data):
    assert len(data)==16
    return bytes(((data[y]>>(7-x))&1)|(((data[y+8]>>(7-x))&1)<<1) for y in range(8) for x in range(8))
def encode_tile(pixels):
    assert len(pixels)==64 and max(pixels)<4
    return bytes(sum(((pixels[y*8+x]>>plane)&1)<<(7-x) for x in range(8)) for plane in range(2) for y in range(8))
def image_tile(pixels,palette):
    im=Image.frombytes('P',(8,8),bytes(pixels));im.putpalette(sum((list(c) for c in palette),[])+[0]*756);return im
