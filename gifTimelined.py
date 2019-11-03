from PIL import Image
import numpy
from pygifsicle import optimize
from threading import Thread
import threading
import multiprocessing
from time import sleep


GIF_FPS = 15
GIF_HEIGH = 1080
GIF_WIDTH = 1920
GIF_FRAMES = 1
COLOR = 255
BAR_SIZE = 0
BAR_HEIGH = 5
P = None

lock = threading.RLock()
thread_limit = multiprocessing.cpu_count() * 2
thread_count = 0
frames = None


# Open the gif.
def gif_open(filename):
    image = Image.open(filename)
    global P
    P = image.getpalette()
    frames = []
    try:
        while True:
            frames.append(numpy.array(image))
            image.seek(image.tell()+1)
    except EOFError:
        pass

    return numpy.asarray(frames) # Transform list of frames into numpy array for convenience.


def add_progress_bar(index):
    global thread_count
    global GIF_HEIGH
    global BAR_HEIGH
    global GIF_FPS
    global BAR_SIZE
    global COLOR
    global frames
    for h in range(GIF_HEIGH):
        if h >= GIF_HEIGH - BAR_HEIGH:
            if f > GIF_FPS - 1:
                for w in range(BAR_SIZE*(index//GIF_FPS)):
                    lock.acquire()
                    frames[index][h][w] = COLOR - frames[index][h][w]
                    lock.release()
    
    lock.acquire()
    thread_count -= 1
    lock.release()


frames = gif_open('test.gif')

GIF_FRAMES = len(frames)
GIF_HEIGH = len(frames[0])
GIF_WIDTH = len(frames[0][0])
BAR_SIZE = GIF_WIDTH//(GIF_FRAMES//GIF_FPS)

threads = []
for f in range(GIF_FRAMES):
    thread = Thread(target=add_progress_bar, args=(f,))
    threads.append(thread)
    
for thread in threads:
    while thread_count == thread_limit:
        sleep(0.01)
    thread_count += 1
    thread.start()

for thread in threads:
    thread.join()
        
# Saving.
gif = []
for f in frames:
    im = Image.fromarray(f, mode='P')
    im.putpalette(P)
    gif.append(im)
gif[0].save('_gif.gif', save_all=True, append_images = gif[1:], loop=0, interlace=True, optimize=True)

# Optimizing a gif
optimize('_gif.gif')

pass