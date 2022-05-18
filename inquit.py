from os.path import splitext
import re
from cltkreaders.lat import LatinLibraryCorpusReader
from latintools import preprocess
import pandas as pd

LL = LatinLibraryCorpusReader()

direct_speech_compile = re.compile(r'["\'´`](.*?)["\'´`]', flags=re.MULTILINE)
bracket_citation_compile = re.compile(r'\[ ?\d+?\w? ?\]')
number_citation_compile = re.compile(r'\d+\w?\. ')
rn_citation_compile = re.compile(r'\b^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b\.?')

def remove_ll_citations(text, **kwargs):
    text = bracket_citation_compile.sub('', text)
    text = rn_citation_compile.sub('', text)
    text = number_citation_compile.sub('', text)
    return text

def is_allcaps(text):
    if preprocess(text, lower=False).isupper():
        return True

def is_allnumbers(text):
    return True if ''.join(text.split()).isnumeric() else False

def is_mostlynumbers(text):
    text = ''.join(text.split())
    return True if sum([c.isnumeric() for c in ''.join(text.split())])/len(text) > .9 else False

def remove_ll_paratext(para, **kwargs):
    if not 'Latin Library' in para or not is_allcaps(para) or not is_allnumbers(para) or is_mostlynumbers(para):
        return para

def extract_direct_speech(sent):
    # Standardize spacing, line breaks
    sent = sent.strip()
    sent = " ".join(sent.split('\n'))

    # Capture cases of 1. introductory quotation mark without match that
    # represents a paragraph of direct speech, or 2. speech that continues
    # from previous paragraph but stops midway (i.e. no introductory mark)

    # Handle M'. praenomen
    sent = sent.replace("M'.", 'M|.')

    if sent.count('"') == 1:
        if sent[0] == '"':
            return sent[1:], None
        else:
            qm_index = sent.find('"')
            if qm_index - 1 == ' ':
                return sent[qm_index+1:], sent[:qm_index-2]
            else:
                return sent[:qm_index], sent[qm_index+2:]

    if sent.count("'") == 1:
        if sent[0] == "'":
            return sent[1:]
        else:
            qm_index = sent.find("'")
            if qm_index - 1 == ' ':
                return sent[qm_index+1:], sent[:qm_index-2]
            else:
                return sent[:qm_index], sent[qm_index+2:]           
    
    def add_placeholders(l):
        if len(l) == 1:
            return f'[ ] {l[0]}'
        return " [ ] ".join(l)


    # Use regex to extract quoted text
    direct_speech = [item for item in direct_speech_compile.findall(sent) if item]
    direct_speech = " ".join([item.strip().replace("M|.", "M'.") for item in direct_speech])
    direct_speech = preprocess(direct_speech, punctuation=True, lower=False)
    indirect_speech = direct_speech_compile.sub('~~~', sent)
    indirect_speech = [item for item in re.split(r'~~~', indirect_speech) if item]
    indirect_speech = add_placeholders([item.strip().replace("M|.", "M'.") for item in indirect_speech])
    indirect_speech = preprocess(indirect_speech, punctuation=True, lower=False)
    return direct_speech, indirect_speech

if __name__ == '__main__':

    citation_compile = re.compile(r'\[ ?\d+?\w? ?\]')
    authors = ['ammianus/', 'curtius/',
                'sall.', 'livy/', 'tacitus/', 'sha/', 
                'caesar/', 'nepos/', 'valmax', 'suetonius/']

    hist = []
    for author in authors:
        for file in LL.fileids():
            if author in file:
                hist.append(file)

    data = []
    files = []

    for file in hist:
        paras = [para for para in LL.paras(file)]
        file_ = file.replace('/', '_')
        files.append(file_)
        for i, para in enumerate(paras):
            if remove_ll_paratext:
                para_ = remove_ll_citations(para, bracket_citation_compile=bracket_citation_compile, rn_citation_compile=rn_citation_compile, number_citation_compile=number_citation_compile).replace("M'.", "M|.")
                if '"' in para_ or "'" in para_:
                    direct_speech = extract_direct_speech(para_)[0]
                    if direct_speech:
                        data.append((file_, para, i, 'speech', direct_speech.strip()))
                    narrative = extract_direct_speech(para_)[1]                            
                    if narrative:
                        data.append((file_, para, i, 'narrative', narrative.strip()))

    # Output with files combined
    for type_ in ['speech', 'narrative']:
        for file_ in files:
            paras_comb =[]
            for file, original, paraid, type, content in data:
                if file == file_ and type == type_:
                    paras_comb.append(content)
            if paras_comb:
                paras_comb = '\n\n'.join(paras_comb)
                file_base = splitext(file_)[0]
                filename = f'{file_base}_{type_}.txt'
                with open(f'data/output/{filename}', 'w') as f:
                    f.write(paras_comb)
