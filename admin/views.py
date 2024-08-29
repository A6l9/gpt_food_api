from sqladmin import ModelView

from database.models import FAQ


class FAQView(ModelView, model=FAQ, path='/faq'):
    name = 'FAQ'