python -m venv venv
venv\Scripts\activate

pip install "django>=3.2, <4.0"
pip install pillow
python manage.py startapp core
pip install -U django-jazzmin
pip install django-shortuuidfield
pip install django-taggit
pip install django django-tinymce
pip install reportlab
pip install mysqlclient
pip install django-import-export openpyxl
pip install psycopg


pip freeze > requirements.txt

python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

python manage.py update_sold_count
python manage.py update_review_count

python manage.py runserver

# Git commnads

git add .
git checkout -b develop
git commit -m ":up: added payment method COD"
git push --set-upstream origin develop


Mobile Device View Div
my-6 block md:hidden

For Business ERP :
Apps:
1. business
2. products
3. sales
4. customers
5. inventory
6. reports
