# coding=utf-8

import sys
import json

if __name__=='__main__':
    if len(sys.argv) != 3:
        sys.stderr.write('Wrong args number!')
    else:
        with open(sys.argv[2],'w') as g:
            sys.stdout = g
            with open(sys.argv[1],'r') as f:
                data = json.load(f)
                sys.stdout.write(json.dumps(data))