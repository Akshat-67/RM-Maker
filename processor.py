from docxtpl import DocxTemplate, RichText
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

    def generate(self, context, output_path, highlight_ai=False, highlight_missing=False, verified_fields=None):
        """
        context: A dictionary containing the data to fill in the template.
        output_path: Where to save the generated .docx file.
        verified_fields: A set of field paths (e.g., "bs.0.n") that are verified.
        """
        if verified_fields is None: verified_fields = set()
        context = self._pad_indexed_lists(context)

        # Apply highlighting if requested
        if highlight_ai or highlight_missing:
            context = self._apply_highlighting(context, verified_fields, highlight_ai, highlight_missing)

        self.doc.render(context)
        self.doc.save(output_path)
        return output_path

    def _apply_highlighting(self, data, verified, h_ai, h_miss, path=""):
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                new_path = f"{path}.{k}" if path else k
                new_data[k] = self._apply_highlighting(v, verified, h_ai, h_miss, new_path)
            return new_data
        elif isinstance(data, list):
            return [self._apply_highlighting(item, verified, h_ai, h_miss, f"{path}.{i}") for i, item in enumerate(data)]
        else:
            val = str(data).strip()
            if not val:
                if h_miss:
                    return RichText("[MISSING]", color="FF0000", bold=True)
                return ""

            # If not verified and h_ai is True, highlight yellow
            if h_ai and path not in verified:
                # We assume if it has a value but is not verified, it was AI filled or needs review
                return RichText(val, highlight="yellow")

            return val

if __name__ == "__main__":
    # Small test if a test_template.docx exists
    pass
