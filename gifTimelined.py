import time
import sys
from PIL import Image
import numpy
from pygifsicle import optimize
from threading import Thread
import threading
import multiprocessing
from time import sleep
from pathlib import Path


GIF_FPS = 15
COLOR = 255
BAR_HEIGH = 5
P = None

lock = threading.RLock()
thread_limit = multiprocessing.cpu_count() * 2
thread_count = 0


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


def add_progress_bar(frames, index):
    global thread_count
    global GIF_FPS, BAR_HEIGH, COLOR
    gif_heigh = len(frames[0])
    gif_width = len(frames[0][0])
    frames_count = len(frames)
    bar_size = gif_width//(frames_count//GIF_FPS)
    
    for h in range(gif_heigh):
        if h >= gif_heigh - BAR_HEIGH:
            if index > GIF_FPS - 1:
                for w in range(bar_size*(index//GIF_FPS)):
                    lock.acquire()
                    frames[index][h][w] = COLOR - frames[index][h][w]
                    lock.release()
    
    lock.acquire()
    thread_count -= 1
    lock.release()


# Getting extended name.
def get_target_path(source_path):
    filename = '{}{}.{}'.format(Path(source_path).stem, '_timelapsed', 'gif')
    target_path = str(Path(Path(source_path).parent) / filename)
    return target_path
        

# Saving.
def gif_save(frames, file_path):
    gif = []
    for f in frames:
        im = Image.fromarray(f, mode='P')
        im.putpalette(P)
        gif.append(im)
    target_path = get_target_path(file_path)
    gif[0].save(target_path, save_all=True, append_images = gif[1:], loop=0, interlace=True, optimize=True)

    # Optimizing a gif
    optimize(target_path)


def main():
    start = time.time()
    file_path = ""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("gif file path: ")
    
    frames = gif_open(file_path)

    frames_count = len(frames)
    
    threads = []
    for f in range(frames_count):
        thread = Thread(target=add_progress_bar, args=(frames, f,))
        threads.append(thread)

    global thread_count    
    for thread in threads:
        while thread_count == thread_limit:
            sleep(0.01)
        thread_count += 1
        thread.start()

    for thread in threads:
        thread.join()

    gif_save(frames, file_path)
    
    end = time.time()
    
    input("\n\nDone in: %.2f seconds. Press enter to exit" % (end - start))


if __name__ == "__main__":
    main()