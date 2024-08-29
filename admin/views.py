from sqladmin import ModelView
from wtforms.fields.simple import TextAreaField

from database.models import FAQ


class FAQView(ModelView, model=FAQ):
    can_view_details = False
    name = 'FAQ'
    form_columns = ['question', 'answer']
    # Определите, какие поля будут отображаться в таблице списка
    column_list = ['question', 'answer']
    column_labels = {
        'question': 'Вопросы',
        'answer': 'Ответы'
    }
    column_formatters = {
        FAQ.answer: lambda model, column: (model.answer[:100] + '...') if len(model.answer) > 100 else model.answer
    }
    # Настройка формы
    form_overrides = {
        'answer': TextAreaField
    }
    form_widget = {
        'answer': TextAreaField(
            render_kw={
                'style': 'height: 500px;'  # Вставка стилей непосредственно
            }
        )
    }


