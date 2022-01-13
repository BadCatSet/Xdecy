import os
import shutil

from PIL import Image

from_path = 'resourcepacks/standard/'
to_path = 'resourcepacks/monostandard/'


def monochrome(im: Image):
    pix = im.load()
    w, h = im.size

    im2 = Image.new('RGBA', (w, h))
    pix2 = im2.load()
    for x in range(w):
        for y in range(h):
            p = pix[x, y]
            r, g, b, *a = p
            c = (r + g + b) // 3
            pix2[x, y] = (c, c, c, *a)
    return im2


for i in os.listdir(from_path):
    if not i.endswith('.png'):
        shutil.copyfile(from_path + i, to_path + i)
    else:
        monochrome(Image.open(from_path + i)).save(to_path + i)
