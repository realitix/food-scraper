import lzma
import json
from util import *


def run():
    with open(path.join(HERE, 'cache', 'step4', 'out.json'), 'rb') as f:
        obj = lzma.LZMAFile(path.join(HERE, 'out', 'out_final.xz'), mode="wb")
        obj.write(f.read())
        obj.close()
    with open(path.join(HERE, 'out', 'out_final_timestamp.json'), 'w') as f:
        json.dump({'timestamp': get_timestamp()}, f)