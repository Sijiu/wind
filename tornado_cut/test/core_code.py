#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/12/4 16:53
"""
import re


def _find_groups(pattern="/([0-9]{4})/([a-z-]+)/"):
    """Returns a tuple (reverse string, group count) for a url.

    For example: Given the url pattern /([0-9]{4})/([a-z-]+)/, this method
    would return ('/%s/%s/', 2).
    """

    pieces = []
    for fragment in pattern.split('('):
        print "fragment  ", fragment
        if ')' in fragment:
            paren_loc = fragment.index(')')
            if paren_loc >= 0:
                pieces.append('%s' + fragment[paren_loc + 1:])
        else:
            pieces.append(fragment)
        print "pieces:  ", pieces

    return (''.join(pieces), re.compile(pattern).groups)

print _find_groups()