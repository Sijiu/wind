#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/9 10:33
"""

import os

def show_fd():
    with open(r"E:\docs\wind\nonado\use_tornado\fs_read.txt", "r") as f:
        fd =  f.fileno()
        print "fd==", fd
        _f = os.fdopen(fd)
        _fd = _f.fileno()
        # print "_fd==", _fd, type(f), type(_f)
        print _f.read(10)

        new_fd = os.dup(fd)
        os.close(_fd)
        print "new_fd==", new_fd
        new_f = os.fdopen(new_fd)
        print "new_f==", new_f.read(20)



if __name__ == '__main__':
    show_fd()