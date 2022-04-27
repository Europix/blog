import unittest
from app import create_app, db
from app.models import User, AnonymousUser, Tag, Article
from flask import json, current_app


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password_hash='cat')
        self.assertTrue(u.password_hash is not None)

    def test_password_verification(self):
        u = User(password_hash='cat')
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password_hash='cat')
        u2 = User(password_hash='cat')
        self.assertFalse(u.password_hash != u2.password_hash)

    def test_invalid_username(self):
        u1 = User(username='cat')
        db.session.add(u1)
        db.session.commit()
        u2 = User(username='dog')
        self.assertFalse(u2.username == u1.username)

    def test_valid_username(self):
        u1 = User(username='valid_username')
        u2 = User(username='valid_username')
        self.assertTrue(u2.username == u1.username)

    def test_roles_and_permissions(self):
        u = User(username='Europixtest', password_hash='root')
        self.assertFalse(u.status, '2')
        self.assertFalse(u.is_admin())

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertTrue(u.is_anonymous)
        self.assertFalse(u.is_admin())

    # Tags
    def test_tags(self):
        t = Tag(name='qwq', visible=True)
        self.assertTrue(t.name, 'qwq')
        self.assertTrue(t.visible)

    def test_tag_duplicated(self):
        t = Tag(name='qwq')
        t2 = Tag(name='qwq')
        db.session.add(t)
        try:
            db.session.add(t2)
        except Exception:
            self.assertTrue(True)

    # Articles
    def test_articles(self):
        t = Article(name='qwq', content='Test Article')
        self.assertTrue(t.name, 'qwq')
        self.assertTrue(t.content, 'Test Article')

    def test_articles_2(self):
        t = Article(name='qwq', content='Test Article')
        self.assertFalse(t.state, '0')
        self.assertFalse(t.vc, '10')
        self.assertFalse(isinstance(t.id, str))

    def test_articles_duplicated(self):
        t = Article(name='qwq', content='Test Article')
        t2 = Article(name='qwq', content='Test Article')
        db.session.add(t)
        try:
            db.session.add(t2)
        except Exception:
            self.assertTrue(True)

    # Flask
    def test_home_page(self):
        response = self.client.get('index.html')
        self.assertTrue('register' not in response.get_data(as_text=True))

    def test_article(self):
        q = Article(title='qwq')
        db.session.add(q)
        db.session.commit()
        qwq = Article.query.filter_by(title='qwq').first()
        self.assertIsNotNone(qwq)

    def test_delete_article(self):
        q = Article(title='qwq')
        db.session.add(q)
        db.session.delete(q)
        db.session.commit()
        qwq = Article.query.filter_by(title='qwq').first()
        self.assertIsNone(qwq)

    def test_edit_article(self):
        q = Article(title='qwq')
        db.session.add(q)
        db.session.commit()
        qwq = Article.query.filter_by(title='qwq').first()
        qwq.title = 'qwqwq'
        db.session.commit()
        self.assertIsNotNone(qwq)

    def test_register(self):
        response = self.client.post('http://localhost:5000/regist', data={
            'email': 'mercury1244Test@outlook.com',
            'name': 'Europix_Unit_Test',
            'password1': '123',
            'password2': '123'})
        self.assertTrue(response.status_code, '200')

    def test_login(self):
        response = self.client.post('http://localhost:5000/login', data={
            'name': 'Europix',
            'password1': 'root',
        })
        self.assertTrue(response.status_code, '200')

    def test_posts(self):
        response = self.client.post(
            'http://localhost:5000/articles',
            data=json.dumps({'body': 'I am a new post'}),
            content_type='application/json')
        self.assertTrue(response.status_code, '200')

    def test_home_pages(self):
        response = self.client.get('http://localhost:5000/')
        self.assertTrue(response.status_code == 200)

    def test_article_pages(self):
        response = self.client.get('http://localhost:5000/article/5/')
        self.assertTrue(response.status_code, '200')

    def test_login_pages(self):
        response = self.client.get('http://localhost:5000/login')
        self.assertTrue(response.status_code == 200)

    def test_app_working(self):
        self.assertFalse(current_app is None)

    def test_app_current_testing(self):
        self.assertTrue(current_app.config['TESTING'])
