#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: mxh @time:2019/5/1 11:22
"""
import datetime
import re


def define():
    pass


class _Option(object):
    def __init__(self, name, default=None, type=str, help=None, metavar=None, multiple=False, file_name=None):
        if default is None and multiple:
            default = []
        self.name = name
        self.type = type
        self.help = help
        self.metavar = metavar
        self.multiple = multiple
        self.file_name = file_name
        self.default = default
        self._value = None

    def value(self):
        return self.default if self._value is None else self._value

    def parse(self, value):
        _parse = {
            datetime.datetime : self._parse_datetime,
            datetime.timedelta: self._parse_timedelta,
            bool              : self._parse_bool,
            str               : self._parse_string,
        }.get(self.type, self.type)
        if self.multiple:
            if self._value is None:
                self._value = []
            for part in value.split(","):
                if self.type in (int, long):
                    # allow ranges of the form X:Y (inclusive at both ends)
                    lo, _, hi = part.partition(":")
                    lo = _parse(lo)
                    hi = _parse(hi) if hi else lo
                    self._value.extend(range(lo, hi + 1))
                else:
                    self._value.append(_parse(part))
        else:
            self._value = _parse(value)
        return self.value()

    def set(self, value):
        if self.multiple:
            if not isinstance(value, list):
                raise Error("Option %r is required to be a list of %s" %
                            (self.name, self.type.__name__))
            for item in value:
                if item != None and not isinstance(item, self.type):
                    raise Error("Option %r is required to be a list of %s" %
                                (self.name, self.type.__name__))
        else:
            if value != None and not isinstance(value, self.type):
                raise Error("Option %r is required to be a %s" %
                            (self.name, self.type.__name__))
        self._value = value

    # Supported date/time formats in our options
    _DATETIME_FORMATS = [
        "%a %b %d %H:%M:%S %Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y%m%d %H:%M:%S",
        "%Y%m%d %H:%M",
        "%Y-%m-%d",
        "%Y%m%d",
        "%H:%M:%S",
        "%H:%M",
    ]

    def _parse_datetime(self, value):
        for format in self._DATETIME_FORMATS:
            try:
                return datetime.datetime.strptime(value, format)
            except ValueError:
                pass
        raise Error('Unrecognized date/time format: %r' % value)

    _TIMEDELTA_ABBREVS = [
        ('hours', ['h']),
        ('minutes', ['m', 'min']),
        ('seconds', ['s', 'sec']),
        ('milliseconds', ['ms']),
        ('microseconds', ['us']),
        ('days', ['d']),
        ('weeks', ['w']),
    ]

    _TIMEDELTA_ABBREV_DICT = dict(
        (abbrev, full) for full, abbrevs in _TIMEDELTA_ABBREVS
        for abbrev in abbrevs)

    _FLOAT_PATTERN = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'

    _TIMEDELTA_PATTERN = re.compile(
        r'\s*(%s)\s*(\w*)\s*' % _FLOAT_PATTERN, re.IGNORECASE)

    def _parse_timedelta(self, value):
        try:
            sum = datetime.timedelta()
            start = 0
            while start < len(value):
                m = self._TIMEDELTA_PATTERN.match(value, start)
                if not m:
                    raise Exception()
                num = float(m.group(1))
                units = m.group(2) or 'seconds'
                units = self._TIMEDELTA_ABBREV_DICT.get(units, units)
                sum += datetime.timedelta(**{units: num})
                start = m.end()
            return sum
        except:
            raise

    def _parse_bool(self, value):
        return value.lower() not in ("false", "0", "f")

    def _parse_string(self, value):
        return value.decode("utf-8")


class Error(Exception):
    pass


class _Options(dict):

    def __getattr__(self, name):
        if isinstance(self.get(name), _Option):
            return self[name].value()

    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance


options = _Options.instance()
