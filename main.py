import uvicorn

from api.routes import get_faq
from preload import *
# from admin.routes import main_page

if __name__ == '__main__':
    print(root_app.routes)
    uvicorn.run(root_app, host="127.0.0.1", port=8000)