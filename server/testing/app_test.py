from app import app
from models import db, Article, User

app.secret_key = b'a\xdb\xd2\x13\x93\xc1\xe9\x97\xef2\xe3\x004U\xd1Z'

class TestApp:
    '''Flask API in app.py'''

    def setup_method(self):
        '''Reset the test database before each test.'''
        with app.app_context():
            db.drop_all()
            db.create_all()

    def test_can_only_access_member_only_while_logged_in(self):
        '''Allows only logged-in users to access /members_only_articles'''
        with app.app_context():
            user = User(username='testuser')
            db.session.add(user)
            db.session.commit()

            article = Article(
                title='Test Member Article',
                content='Content',
                is_member_only=True
            )
            db.session.add(article)
            db.session.commit()

            user_id = user.id

        with app.test_client() as client:
            client.get('/clear')
            client.post('/login', json={'username': 'testuser'})

            response = client.get('/members_only_articles')
            assert response.status_code == 200

            client.delete('/logout')
            response = client.get('/members_only_articles')
            assert response.status_code == 401

    def test_member_only_articles_shows_member_only_articles(self):
        '''Only shows member-only articles on index route'''
        with app.app_context():
            user = User(username='testuser')
            db.session.add(user)

            member_article = Article(
                title='Member Only',
                content='Secret',
                is_member_only=True
            )
            regular_article = Article(
                title='Regular',
                content='Public',
                is_member_only=False
            )
            db.session.add_all([member_article, regular_article])
            db.session.commit()

        with app.test_client() as client:
            client.get('/clear')
            client.post('/login', json={'username': 'testuser'})

            response = client.get('/members_only_articles')
            assert response.status_code == 200

            response_json = response.get_json()
            assert len(response_json) == 1
            assert response_json[0]['title'] == 'Member Only'
            assert response_json[0]['is_member_only'] is True

    def test_can_only_access_member_only_article_while_logged_in(self):
        '''Allows full access to a member-only article only if logged in'''
        with app.app_context():
            user = User(username='testuser')
            db.session.add(user)
            db.session.commit()

            article = Article(
                title='Member Only',
                content='Secret',
                is_member_only=True
            )
            db.session.add(article)
            db.session.commit()
            article_id = article.id

            regular_article = Article(
                title='Regular',
                content='Public',
                is_member_only=False
            )
            db.session.add(regular_article)
            db.session.commit()
            regular_id = regular_article.id

        with app.test_client() as client:
            client.get('/clear')

            # Not logged in - should get 401
            response = client.get(f'/members_only_articles/{article_id}')
            assert response.status_code == 401

            client.post('/login', json={'username': 'testuser'})
            response = client.get(f'/members_only_articles/{article_id}')
            assert response.status_code == 200
            assert response.get_json()['title'] == 'Member Only'

            # Even if logged in, regular articles shouldn't be accessed via members-only route
            response = client.get(f'/members_only_articles/{regular_id}')
            assert response.status_code == 404
