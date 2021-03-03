import obeliks

import classla
from classla import Document
from classla.models.common.conll import CoNLLFile

from . euannotation import EUTermAnnotator
from . classification import DocClassifier


class MarcellPipeline:

    def __init__(self):
        # Set up stanfordnlp pipeline
        self.classla_pipeline = classla.Pipeline('sl', processors='tokenize,ner,pos,lemma,depparse', 
                tokenize_pretokenized=True, use_gpu=True)

        self.eu_term_annotator = EUTermAnnotator()
        self.doc_classifier = DocClassifier()

        self.meta_fields = ['language', 'date', 'title', 'type', 'entype']

    def create_conllup_metadata(self, standoff_metadata):
        res = []

        res.append('# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC MARCELL:NE MARCELL:NP MARCELL:IATE MARCELL:EUROVOC MARCELL:EUROVOCMT')
        res.append('# newdoc id = {}'.format(standoff_metadata['doc_id']))

        for key in self.meta_fields:
            if key not in standoff_metadata:
                raise InvalidParams('Missing key "{}" in standoff metadata.'.format(key))

            val = standoff_metadata[key]
            val = val.replace('\n', ' ').replace('\r', '')

            res.append('# {} = {}'.format(key, val))

        return res

    def run_classla(self, text, standoff_metadata):
        # Because we already have CoNLL-U formated input, we need to skip the tokenization step.
        # This currently done by setting the Documents text parameter as None. After that we also
        # have to manually create a CoNLLFile instance and append it to the Document.
        doc = Document(text=None)
        conll_file = CoNLLFile(input_str=text)
        doc.conll_file = conll_file

        # Start Classla processing.
        res = self.classla_pipeline(doc)

        rows = []
        for line in res.conll_file.conll_as_string().splitlines():
            if not line.startswith('#') and len(line) > 0 and not line.isspace():
                # Because stanfordnlp returns in the basic CONLLU format, we need to move
                # the NER values from the MISC column to a separate one.
                vals = line.split('\t')

                # Add empty columns to fit the CONLLU Plus format.
                vals += 4 * ['_']

                misc_vals = vals[9].split('|')

                new_misc = []
                for misc_val in misc_vals:
                    if misc_val.startswith('NER='):
                        vals[10] = misc_val.replace('NER=', '')
                    else:
                        new_misc.append(misc_val)

                if len(new_misc) == 0:
                    vals[9] = '_'
                else:
                    vals[9] = '|'.join(new_misc)


                rows.append('\t'.join(vals))
            else:
                rows.append(line)

        return rows

    def process(self, text, standoff_metadata):
        metadata_rows = self.create_conllup_metadata(standoff_metadata)

        # Obeliks
        obeliks_res = obeliks.run(text=text, conllu=True, pass_newdoc_id=True)

        # Classla
        rows = self.run_classla(obeliks_res, standoff_metadata)

        # IATE
        rows = self.eu_term_annotator.process_iate(rows)

        # EUROVOC
        rows = self.eu_term_annotator.process_eurovoc(rows)

        # EUROVOC-MT
        rows = self.eu_term_annotator.process_eurovocmt(rows)

        # Classify whole document based on IATE and EUROVOC annotations
        doc_type = self.doc_classifier.classify(rows)
        if doc_type:
            metadata_rows.append('# {} = {}'.format('category', doc_type))

        metadata_rows.append('\n')
        res = metadata_rows + rows 
        return '\n'.join(res)

