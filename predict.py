#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import re, collections, csv
import os
import pickle

settings_dir = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.dirname(settings_dir))
alphabet = 'abcdefghijklmnopqrstuvwxyzáéíóúñü'.decode('utf-8')
numbers = {1:".", 2:"abc", 3:"def", 4:"ghi", 5:"jkl", 6:"mnño".decode('utf-8'), 7:"pqrs", 8:"tuv", 9:"wxyz"}
LAMB1 = float(0.1)
LAMB2 = float(0.3)
LAMB3 = float(0.6)
LAMB4 = float(0)


def words(text): return re.findall('[a-záéíóúñü]+'.decode('utf-8'), text.decode('utf-8').lower())



def train(features):
    words = collections.defaultdict(lambda: 1)
    letters = collections.defaultdict(lambda: 0)
    cgrams = [0,0,0,0]

    before = ""
    for f in features:
        words[f] += 1

        f = " " + f
        for c in f:
            letters[c] += 1
            cgrams[1] += 1

            if len(before) > 0:
                letters[before[-1:]+c] += 1
                cgrams[2] += 1
            if len(before) > 1:
                letters[before[-2:]+c] += 1

            if len(before) > 2:
                letters[before[-3:]+c] += 1

            before += c

        if before > 5: before = before[-5:]


    #calculate  4grams prob.
    for gram in letters.keys():
        if len(gram) == 4:
            letters[gram] = float(letters[gram]) / letters[gram[:3]]

    #calculate trigrams prob.
    for gram in letters.keys():
        if len(gram) == 3:
            letters[gram] = float(letters[gram]) / letters[gram[:2]]

    #calculate bigrams prob.
    for gram in letters.keys():
        if len(gram) == 2:
            letters[gram] = float(letters[gram]) / letters[gram[0]]

    #calculate unigrams prob.
    for gram in letters.keys():
        if len(gram) == 1: letters[gram] = float(letters[gram]) / cgrams[1]



    return words,letters

def read_dict(files):
    data = ''
    for file in files:
        with open(file, 'r') as f:
            data += ' ' + f.read()

    return data


def mix(f1, f2):
    for f in f2.keys():
        if f in f1: f1[f] = (f1[f] + f2[f])/2
        else: f1[f] = f2[f]

    return f1

WORDS = read_dict([os.path.join(PROJECT_ROOT, 'data/libros.txt')])

NWORDS, NLETTERS = train( words( WORDS ) )


def edits1(word):
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in alphabet if b]
   inserts    = [a + c + b     for a, b in splits for c in alphabet]
   return set(deletes + transposes + replaces + inserts)

def edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1))

def edits3(word):
    return set(e2 for e1 in edits2(word) for e2 in edits1(e1))

def edits4(word):
    return set(e2 for e1 in edits3(word) for e2 in edits1(e1))

def known(words): return set(w for w in words if w in NWORDS)

def unknown(words): return set(w for w in words if not w in NWORDS)

def candidates(word):
    #word = word.decode('utf-8')
    kn = known([word])
    #if len(kn) > 0: return kn
    return (known(edits1(word)).union(known(edits2(word))).union(kn))

def getletter(n, before):
    prob = 0;
    ch = ''

    if before == "": before = " "
    for c in numbers[n]:
        pc =  LAMB1 * NLETTERS[c] + \
              (LAMB2 * NLETTERS[before[-1:] + c] if len(before) > 0 else 0) + \
              (LAMB3 * NLETTERS[before[-2:] + c] if len(before) > 1 else 0) + \
              (LAMB4 * NLETTERS[before[-3:] + c] if len(before) > 2 else 0)

        if prob < pc:
            prob = pc
            ch = c

    return ch


def correct(word):

    cand = candidates(word)

    if len(cand) == 0: return []

    #take candidates and their frecuencies
    cand = [{'sug':c, 'frec':NWORDS[c]} for c in cand]


    #calculate accumulated frequency
    cand = sorted(cand, reverse=True)
    acu = 0
    for c in cand:
        acu += c['frec']
        c['frec_acu'] = acu

    
    #return the 80%
    if( len(cand) > 10):
        max = acu * 0.8
        cand = [c for c in cand if c['frec_acu'] < max]

        cand = cand[:10]
    

    return cand

def predict(numbers):
    prediction = ''

    before = " "
    for n in numbers:
        if n != " ":
            if len(prediction) > 0: before = prediction[-1:]
            if len(prediction) > 1: before = prediction[-2:]
            prediction += getletter(int(n), before)
        else:
            prediction += " "

    return prediction

def mark(s1, s2):
    return float(sum([c1==c2 for c1,c2 in zip(s1,s2)]))


def main(word, numbers):
    tg1 = "to s"
    tg2 = "to p"
    print LAMB4 * NLETTERS[tg1]  + LAMB3 * NLETTERS[tg1] +  LAMB2 * NLETTERS[tg1[-2:]]  +  LAMB1 * NLETTERS[tg1[-1:]]
    print LAMB4 * NLETTERS[tg2] +  LAMB3 * NLETTERS[tg2] +  LAMB2 * NLETTERS[tg2[-2:]]  +  LAMB1 * NLETTERS[tg2[-1:]]

    print "algoritmo de texto predictivo"
    print predict(numbers)

    print mark(predict(numbers), "algoritmo de texto predictivo")
    print mark("aliositmo de vezvo prefibuguo", "algoritmo de texto predictivo")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description='T9 prediction')

    parser.add_argument(
            '--word',
            option_strings=['--w'], metavar='word', type=str,
            default='sheet.data', help='Word to correct')

    parser.add_argument(
            '--numbers',
            option_strings=['--w'], metavar='numbers', type=str,
            default='sheet.data', help='Numbers to predict a word')

    args = parser.parse_args()

    main(args.word, args.numbers)