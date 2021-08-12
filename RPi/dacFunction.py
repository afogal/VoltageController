from noGUI import *
import time

if __name__ == "__main__":
    i=0
    start = time.time()
    while True:
        do_update_dac(2*np.sin(time.time()-start)+3,0)
