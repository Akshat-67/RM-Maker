from docxtpl import DocxTemplate
import os

class TemplateProcessor:
    def __init__(self, template_path):
        self.template_path = template_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found at {template_path}")
        self.doc = DocxTemplate(template_path)

    def generate(self, context, output_path):
        """
        context: A dictionary containing the data to fill in the template.
        output_path: Where to save the generated .docx file.
        """
        self.doc.render(context)
        self.doc.save(output_path)
        return output_path

if __name__ == "__main__":
    # Small test if a test_template.docx exists
    pass
