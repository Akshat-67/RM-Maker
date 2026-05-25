from docxtpl import DocxTemplate
import os
import re
import zipfile
from html import unescape

LIST_DEFAULTS = {
    "bs": {"s": "", "n": "", "a": "", "r": "", "rn": "", "adr": "", "id": ""},
    "ls": {"n": "", "a": "", "w": "", "t": ""},
    "ps": {"adr": "", "n": "", "s": "", "e": "", "w": ""},
    "ws": {"n": "", "r": "", "rn": "", "adr": ""},
    "ds": {"t": ""},
}


class TemplateProcessor:
    def __init__(self, template_path):
        self.template_path = template_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")
        self.doc = DocxTemplate(template_path)

    def _template_xml(self):
        parts = []
        with zipfile.ZipFile(self.template_path) as zf:
            for name in zf.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    xml = zf.read(name).decode("utf-8", errors="ignore")
                    parts.append(re.sub(r"<[^>]+>", "", xml))
        return unescape("\n".join(parts))

    def _required_list_lengths(self):
        required = {}
        for list_name, index in re.findall(r"\b(bs|ls|ps|ws|ds)\s*\[\s*(\d+)\s*\]", self._template_xml()):
            required[list_name] = max(required.get(list_name, 0), int(index) + 1)
        return required

    def _pad_indexed_lists(self, context):
        for list_name, size in self._required_list_lengths().items():
            values = context.get(list_name)
            if not isinstance(values, list):
                values = []
            while len(values) < size:
                values.append(LIST_DEFAULTS[list_name].copy())
            context[list_name] = values
        return context

    def generate(self, context, output_path):
        """
        context: A dictionary containing the data to fill in the template.
        output_path: Where to save the generated .docx file.
        """
        context = self._pad_indexed_lists(context)
        self.doc.render(context)
        self.doc.save(output_path)
        return output_path

if __name__ == "__main__":
    # Small test if a test_template.docx exists
    pass
