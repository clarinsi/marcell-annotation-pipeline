import re
import collections
from pathlib import Path


class DocClassifier:

    def __init__(self):
        # Load mapping file
        res_path = Path(__file__).parent / 'res/'
        self.type_map = self.load_doctype_mapping(res_path / 'eurovoc-doctype-map.txt')
    
    @staticmethod
    def load_doctype_mapping(mapping_file):
        type_map = dict()
        with open(mapping_file, 'r') as f:
            for line in f:
                line = line.strip()
                key, val = line.split('\t')
                type_map[key] = val[:2]
        return type_map

    @staticmethod
    def extract_iate_doctype(field):
        res = []
        if field != '_':
            annotations = field.split(';')
            for annotation in annotations:
                # Check if it's only a term range marker
                if ':' not in annotation:
                    continue
                annotation = annotation.split(':', 1)[1]
                if '-' not in annotation:
                    continue
                eurovoc_part = annotation.split('-', 1)[1]
                eurovoc_ids = eurovoc_part.split(',')
                for eurovoc_id in eurovoc_ids:
                    res.append(eurovoc_id[:2])
        return res

    @staticmethod
    def extract_eurovoc_ids(field):
        res = []
        if field != '_':
            annotations = field.split(';')
            for annotation in annotations:
                # Check if it's only a term range marker
                if ':' not in annotation:
                    continue
                annotation = annotation.split(':', 1)[1]
                res.append(annotation)
        return res

    def classify(self, doc_rows):
        doctype_ids = []

        for line in doc_rows:
            line = line.strip()
            if len(line) == 0 or not line[0].isnumeric():
                continue

            tokens = line.split('\t')

            # Extract IDs from MARCELL:IATE string
            for doctype_id in self.extract_iate_doctype(tokens[12]):
                doctype_ids.append(doctype_id)

            # Extract IDs from MARCELL:EUROVOC string
            for eurovoc_id in self.extract_eurovoc_ids(tokens[13]):
                if eurovoc_id in self.type_map:
                    doctype_ids.append(self.type_map[eurovoc_id])

        if len(doctype_ids) == 0:
            return None

        # Count up results
        counter = collections.Counter(doctype_ids)

        # Return most common doc type
        return counter.most_common(1)[0][0]

