from mdutils.mdutils import MdUtils

class ContextBuilder:
    def __init__(self, title="Контекст для оценки стоимости автомобиля"):
        self.mdFile = MdUtils(file_name='context', title=title)
        self.sections = []

    def add_photo_analysis_section(self, photo_description, analysis_result):
        section = f"## Анализ фотографии\n{photo_description}\n\n**Результат анализа:** {analysis_result}\n"
        self.sections.append(section)

    def add_textual_info_section(self, textual_info):
        section = f"## Текстовая информация\n{textual_info}\n"
        self.sections.append(section)

    def generate_context(self):
        for section in self.sections:
            self.mdFile.new_paragraph(section)
        return self.mdFile.get_md_string()