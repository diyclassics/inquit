import re
from cltkreaders.lat import LatinLibraryCorpusReader

LL = LatinLibraryCorpusReader()

direct_speech_compile = re.compile(r'[^M]?["\'´](.*?)["\'´]', flags=re.MULTILINE)
bracket_citation_compile = re.compile(r'\[ ?\d+?\w? ?\]')
rn_citation_compile = re.compile(r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\.?')

def remove_ll_citations(text, **kwargs):
    text = bracket_citation_compile.sub('', text)
    text = rn_citation_compile.sub('', text)
    return text

def extract_direct_speech(sent):
    # Standardize spacing, line breaks
    sent = sent.strip()
    sent = " ".join(sent.split('\n'))

    # Capture cases of 1. introductory quotation mark without match that
    # represents a paragraph of direct speech, or 2. speech that continues
    # from previous paragraph but stops midway (i.e. no introductory mark)

    # Handle M'. praenomen
    sent = sent.replace("M'.", 'M`.')

    if sent.count('"') == 1:
        if sent[0] == '"':
            return sent[1:]
        else:
            qm_index = sent.find('"')
            if qm_index - 1 == ' ':
                return sent[qm_index+1:]
            else:
                return sent[:qm_index]

    if sent.count("'") == 1:
        if sent[0] == "'":
            return sent[1:]
        else:
            qm_index = sent.find("'")
            if qm_index - 1 == ' ':
                return sent[qm_index+1:]
            else:
                return sent[:qm_index]                
    
    # Use regex to extract quoted text
    direct_speech = direct_speech_compile.findall(sent)
    return " ".join([item.strip() for item in direct_speech])

if __name__ == '__main__':

    citation_compile = re.compile(r'\[ ?\d+?\w? ?\]')
    authors = ['sall.', 'livy/', 'curtius/', 'tacitus/', 'sha/']

    hist = []
    for author in authors:
        for file in LL.fileids():
            if author in file:
                hist.append(file)

    for file in hist:
        paras = [para for para in LL.paras(file)]
        file_ = file.replace('/', '_')
        with open(f'data/output/ds_{file_}', 'w') as f:
            for para in paras:
                para_ = remove_ll_citations(para, bracket_citation_compile=bracket_citation_compile, rn_citation_compile=rn_citation_compile).replace("M'.", "M`.")
                if '"' in para_ or "'" in para_:
                    f.write('-----\n')
                    f.write(f'Original: {para}\n')
                    f.write(f'Direct: "{extract_direct_speech(para_)}"\n')    
                    f.write('-----\n')
                    f.write('\n')
