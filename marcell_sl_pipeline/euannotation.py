import json
from pathlib import Path


class EUTermAnnotator:

    def __init__(self):
        self.asc_punct = u'!"#$%&\'()*+,./:;<=>?[\\]^`{|}~'
        # no - and _
        self.uni_punct = b'\xe2\x80\x98\xe2\x80\x99\xe2\x80\x9a\xe2\x80\x9b\xe2\x80\x9c\xe2\x80\x9d\xe2\x80\x9e\xe2\x80\x9f\xe2\x80\xa6'.decode(
            'utf-8')
        # U+2018 \xe2\x80\x98 left single quotation mark
        # U+2019 \xE2\x80\x99 right single quotation mark
        # U+201A \xE2\x80\x9a single low-9 quotation mark
        # U+201B \xE2\x80\x9b single high-reversed-9 quotation mark
        # U+201C \xe2\x80\x9c left double quotation mark
        # U+201D \xe2\x80\x9d right double quotation mark
        # U+201E \xe2\x80\x9e single high-reversed-9 quotation mark
        # U+201F \xe2\x80\x9f double high-reversed-9 quotation mark
        # U+2026 \xe2\x80\xa6 horizontal ellipsis

        res_path = Path(__file__).parent / 'res/'
        self.terms_iate = json.load(open(res_path / 'iate.json'))
        self.terms_eurovoc = json.load(open(res_path / 'eurovoc.json'))

    def __get_sents(self, conllup_text):
        def line_gen(s):
            buff = []
            for c in s:
                if c == '\n':
                    yield ''.join(buff)
                    buff = []
                else:
                    buff.append(c)
            if len(buff) > 0:
                return ''.join(buff)

        sent = []
        for line in line_gen(conllup_text):
            line = line.strip()
            if line.startswith('#'):
                tokens = ['#', line[1:].strip()]
                sent.append(tokens)
                continue
            if len(line) > 0:
                tokens = line.split('\t')
                sent.append(tokens)
            else:
                if len(sent) > 0:
                    yield sent
                sent = []
        if len(sent) > 0:
            yield sent

    def __punct_only(self, word):  # unicode
        punct = set(self.asc_punct + self.uni_punct)
        punct_found = False
        for c in punct:  # unicode
            if c == word:
                punct_found = True
                break
        return punct_found

    def __sent_append(self, sent, word):
        if len(sent):
            sent += ' ' + word
        else:
            sent = word
        return sent

    def __find_text(self, where, text):  # on word boundaries
        text = text.lower()
        where = where.lower()
        tb = text + u' '
        btb = u' ' + text + u' '
        bt = u' ' + text
        rc = False
        if where == text:
            rc = True
        elif where.startswith(tb):
            rc = True
        elif btb in where:
            rc = True
        elif where.endswith(bt):
            rc = True
        return rc

    def __process(self, conllup_text, terms, col_idx):
        out = []
        prev_sent_id = ''
        for sent in self.__get_sents(conllup_text):
            sent_id = ''
            lemma_sent = ''
            for tokens in sent:
                if tokens[0] == '#':
                    words = tokens[1].split()
                    if len(words) > 0:
                        if words[0] == 'sent_id' and words[1] == '=':
                            sent_id = words[2]
                    continue

                # Append columns if needed.
                len1 = len(tokens)
                if col_idx > len1:
                    adc = col_idx - len1
                    for jj in range(adc):
                        tokens.append('_')

                # Reset Eurovoc column.
                tokens[col_idx-1] = '_'

                form = tokens[1]
                lemma = tokens[2]
                upos = tokens[3]
                if not self.__punct_only(lemma):
                    lemma_sent = self.__sent_append(lemma_sent, tokens[2])
            if len(sent_id) == 0:
                sent_id = prev_sent_id
            prev_sent_id = sent_id
            lemma_sent = lemma_sent.replace(' - ', '-').replace(' _ ', '_')

            uni_lemma_sent = lemma_sent
            found_id = 0
            new_sent = sent
            sent_rebuild = False
            iate_ids = []

            # Find only longest match (redmine issue #1616)
            matches = dict()
            for item in terms:
                lemma = item['lemma']
                if self.__find_text(uni_lemma_sent, lemma):
                    # Remove past matches, that are substrings of this one.
                    # If this lemma is a substring of a past match, ignore it.
                    skip = False
                    for p_lemma in list(matches):
                        if lemma.find(p_lemma) != -1:
                            matches.pop(p_lemma)
                        elif p_lemma.find(lemma) != -1:
                            skip = True
                            break

                    if not skip:
                        matches[lemma] = item

            for lemma, item in matches.items():
                found_id += 1
                iate_id = item['id']

                # check if this iate_id was already used
                found = False
                for _id in iate_ids:
                    if _id == iate_id:
                        found = True
                if found:
                    continue
                else:
                    iate_ids.append(iate_id)

                iate_sent = item['tokens']
                ii = 0
                iate_tokens = iate_sent[ii]
                new_sent = []
                id_printed = False

                for tokens in sent:
                    len1 = len(tokens)
                    if tokens[0] == '#':
                        new_sent.append(tokens)
                        continue
                    lemma = tokens[2]
                    iate_lemma = iate_tokens[2]
                    if lemma.lower() == iate_lemma.lower():  # found lemma
                        ii += 1
                        if col_idx > len1:  # append columns, if needed
                            adc = col_idx - len1
                            for jj in range(adc):
                                tokens.append('_')
                            len1 = len(tokens)

                        if tokens[col_idx-1] == '_':
                            if not id_printed:
                                tokens[col_idx-1] = '{}:'.format(found_id) + \
                                    iate_id
                                id_printed = True
                            else:
                                tokens[col_idx-1] = '{}'.format(found_id)
                        else:
                            if not id_printed:
                                tokens[col_idx-1] += ';{}:'.format(found_id) + \
                                    iate_id
                                id_printed = True
                            else:
                                tokens[col_idx-1] += ';{}'.format(found_id)

                        if ii >= len(iate_sent):  # found all lemmas
                            id_printed = False
                            ii = 0
                    else:  # not found lemma
                        if col_idx > len1:  # append columns, if needed
                            adc = col_idx - len1
                            for jj in range(adc):
                                tokens.append('_')
                            len1 = len(tokens)

                        id_printed = False
                        ii = 0
                    new_sent.append(tokens)
                    iate_tokens = iate_sent[ii]
                # end for tokens in sent
                sent_rebuild = True
            # end if find_text
            sent = new_sent

            if not sent_rebuild:
                new_sent = []
                for tokens in sent:
                    len1 = len(tokens)
                    if tokens[0] == '#':
                        new_sent.append(tokens)
                        continue
                    if col_idx > len1:  # append columns, if needed
                        adc = col_idx - len1
                        for jj in range(adc):
                            tokens.append('_')
                        len1 = len(tokens)
                    new_sent.append(tokens)
                # end for tokens in sent
                sent = new_sent

            for tokens in sent:
                if tokens[0] == '#':
                    out.append(tokens[0] + tokens[1])
                else:
                    out.append('\t'.join(tokens))
                out.append('\n')
            out.append('\n')

        return ''.join(out)

    def process_iate(self, conllup_text, col_idx=13):
        return self.__process(conllup_text, col_idx=col_idx, terms=self.terms_iate)

    def process_eurovoc(self, conllup_text, col_idx=14):
        return self.__process(conllup_text, col_idx=col_idx, terms=self.terms_eurovoc)
