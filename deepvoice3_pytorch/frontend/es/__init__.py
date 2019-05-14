# coding: utf-8
from deepvoice3_pytorch.frontend.text.symbols import symbols

import nltk
from random import random

n_vocab = len(symbols)


def text_to_sequence(text, p=0.0):
    from deepvoice3_pytorch.frontend.text import text_to_sequence
    text = text_to_sequence(text, ["basic_cleaners"])
    return text

def sequence_to_text(seq):
    return "".join(chr(n) for n in seq)

from deepvoice3_pytorch.frontend.text import sequence_to_text
