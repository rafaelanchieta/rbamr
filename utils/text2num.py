# -*- coding:utf-8 -*-

# This library is a simple implementation of a function to convert textual
# numbers written in English into their integer representations.
#
# This code is open source according to the MIT License as follows.
#
# Copyright (c) 2008 Greg Hewgill
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# modify to portuguese

import re

ordinal = {
    'primeiro': 1,
    'segundo': 2,
    'terceiro': 3,
    'quarto': 4,
    'quinto': 5,
    'sexto': 6,
    'setimo': 7,
    'oitavo': 8,
    'nono': 9,
    'decimo': 10
}

Small = {
    'zero': 0,
    'um': 1,
    'dois': 2,
    'três': 3,
    'quatro': 4,
    'cinco': 5,
    'seis': 6,
    'sete': 7,
    'oito': 8,
    'nove': 9,
    'dez': 10,
    'onze': 11,
    'doze': 12,
    'treze': 13,
    'quatorze': 14,
    'catorze': 14,
    'quinze': 15,
    'dezesseis': 16,
    'dezessete': 17,
    'dezoito': 18,
    'dezenove': 19,
    'vinte': 20,
    'trinta': 30,
    'quarenta': 40,
    'cinquenta': 50,
    'sessenta': 60,
    'setenta': 70,
    'oitenta': 80,
    'noventa': 90
}

Magnitude = {
    'mil': 1000,
    'milhão': 1000000,
    'bilhão': 1000000000,
    'trilhão': 1000000000000,
    'quatrilhão': 1000000000000000,
    'quintilhão': 1000000000000000000,
    'sextilhão': 1000000000000000000000,
    'septilhão': 1000000000000000000000000,
    'octilhão': 1000000000000000000000000000,
    'nonilhão': 1000000000000000000000000000000,
    'decilhão': 1000000000000000000000000000000000,
}


class NumberException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


def text2num(s):
    a = re.split(r"[\s-]+", s)
    n = 0
    g = 0
    for w in a:
        x = Small.get(w, None)
        if x is not None:
            g += x
        elif w == "cem" and g != 0:
            g *= 100
        else:
            x = Magnitude.get(w, None)
            if x is not None:
                n += g * x
                g = 0
            else:
                return s
                #raise NumberException("Unknown number: " + w)
    return n + g


def ordinal2num(ord):
    for key, value in ordinal.items():
        if key == ord:
            return value


if __name__ == "__main__":
    print ordinal2num('primeiro')
    print text2num('dois')
    print text2num('seis')
    print text2num('duas')
    print text2num('quatro')
    assert 1 == text2num("um")
    assert 12 == text2num("doze")
    assert 72 == text2num("setenta dois")