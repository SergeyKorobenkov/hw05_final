from django.core import mail
from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from .models import Post
from .forms import PostForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
import time
User = get_user_model() 




class UserTest(TestCase):
      def setUp(self):
            self.client = Client()
            self.user = User.objects.create_user(
                  username="test_user", email="connor.s@skynet.com", password="12345"
                )
            small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
            )
            image = SimpleUploadedFile('small.gif', small_gif, content_type='image/gif')
            self.post = Post.objects.create(text="You're talking about things I haven't done yet in the past tense. It's driving me crazy!",
            author=self.user, pub_date='10.02.2020', image=image)
      
      def test_send_email(self):
            # Пользователь регистрируется и ему отправляется письмо с подтверждением регистрации
            # Метод send_mail отправляет email сообщения.
            mail.send_mail(
            'Тема письма', 'Текст письма.',
            'from@rocknrolla.net', ['to@mailservice.com'],
            fail_silently=False, # выводить описание ошибок
            )
            # Проверяем, что письмо лежит в исходящих
            self.assertEqual(len(mail.outbox), 1)
            # Проверяем, что тема первого письма правильная.
            self.assertEqual(mail.outbox[0].subject, 'Тема письма')
      
      def test_profile(self):
            # После регистрации пользователя создается его персональная страница (profile)
            response = self.client.get("/test_user/")
            self.assertEqual(response.status_code, 200)
      
      def test_create_post(self):
            # Авторизованный пользователь может опубликовать пост (new)
            self.client.login(username='test_user', password='12345')
            response = self.client.post('/new/', {'text':'создаем тестовый пост'})
            self.assertEqual(response.status_code, 302)
            cache.clear()
            response1 = self.client.get('/')
            self.assertContains(response1, text = 'создаем тестовый пост')
      
      def test_redirect(self):
            # Неавторизованный посетитель не может опубликовать пост (его редиректит на страницу входа)
            response = self.client.get('/new/')
            self.assertRedirects(response, '/auth/login/?next=/new/', status_code=302, 
            target_status_code=200, msg_prefix='', fetch_redirect_response=True)
      
      def test_accept_post(self):
            # После публикации поста новая запись появляется на главной странице сайта (index), 
            # на персональной странице пользователя (profile), и на отдельной странице поста (post)
            self.client.login(username='test_user', password='12345')
            post_text = "Костыль? Возможно..."
            self.post = Post.objects.create(text=post_text, author=self.user)
            post_id = self.post.pk
            response = self.client.get('/') # проверка для главной страницы
            self.assertContains(response, post_text)
            response1 = self.client.get('/test_user/') # проверка на профиле
            self.assertContains(response1, post_text)
            response2 = self.client.get(f'/test_user/{post_id}/') # проверка для страницы поста
            self.assertContains(response2, post_text)
      
      def test_edit_post(self):
            # Авторизованный пользователь может отредактировать свой пост и его содержимое
            # изменится на всех связанных страницах
            self.client.login(username='test_user', password='12345')
            post_text = "Еще один костыль? А не много ли с тебя?"
            post_id = self.post.pk
            self.post = Post.objects.create(text=post_text, author=self.user)
            response = self.client.post(f'/test_user/{post_id}/edit/', {'text':'ну, может это не так уж и плохо'})
            cache.clear()
            self.assertEqual(response.status_code, 302)
            response1 = self.client.get('/') #на главной странице
            self.assertContains(response1, text = 'ну, может это не так уж и плохо', count=1)
            response2 = self.client.get('/test_user/') # проверка на профиле
            self.assertContains(response2, text = 'ну, может это не так уж и плохо', count=1)
            response3 = self.client.get(f'/test_user/{post_id}/') # проверка для страницы поста
            self.assertContains(response3, text = 'ну, может это не так уж и плохо', count=1)
      
      def test_wrong_edit(self):
            # Проверка на то что пользователь не может редактировать чужой пост
            self.user = User.objects.create_user(
                  username="test_user1", password="12345"
                )
            self.client.login(username='test_user1', password='12345')
            response = self.client.post('/test_user/1/edit/')
            self.assertRedirects(response, '/test_user/1/', status_code=302, target_status_code=200, 
            msg_prefix='', fetch_redirect_response=True)
      

      def test_404(self):
            # Проверка что мы не можем найти страницу 
            response = self.client.get('/404/')
            self.assertEquals(response.status_code, 404)


      def test_image(self):
            # Проверка наличия тега изображения на странице
            post_id = self.post.pk
            response = self.client.get('/test_user/')   # На странице профиля
            self.assertContains(response, '<img')
            response1 = self.client.get('')    # На главной странице
            self.assertContains(response1, '<img')
            response2 = self.client.get(f'/test_user/{post_id}/')   # На странице просмотра поста
            self.assertContains(response2, '<img')
      

      def test_cache(self):
            self.client.login(username='test_user', password='12345')
            post_text = "Проверка кеша"
            self.post = Post.objects.create(text=post_text, author=self.user)
            time.sleep(20)
            response1 = self.client.get('/') 
            self.assertContains(response1, text = 'Проверка кеша', count=1)


      def test_non_image_protection(self):
        # Проверяем что нельзя загрузить не графический файл
        with open('tstdoc.doc', 'rb') as doc:
            response = self.client.post('/new/', {'text': 'I am a test post with image', 'image': doc}, follow=True)
            self.assertNotContains(response, '<img', status_code=200, msg_prefix='', html=False)
      

class FollowCaseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
                        username="TestUser", password="123456"
                )
        self.user2 = User.objects.create_user(
                        username="TestUser2", password="321654"
                )
        self.user3 = User.objects.create_user(
                        username="TestUser3", password="987654"
                )
        
        self.post = Post.objects.create(text="Test post", author=self.user3)


    def test_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок."""
        self.client.login(username="TestUser", password="123456")
        self.client.get('/TestUser2/follow')
        response = self.client.get('/TestUser/')
        self.assertEqual(response.status_code, 200)
        self.client.get('/TestUser2/unfollow')
        response = self.client.get('/TestUser/')
        self.assertEqual(response.status_code, 200)
    

    def test_news_lent(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан и не появляется в ленте тех, кто не подписан на него."""
        self.client.login(username="TestUser", password="123456")
        self.client.get('/TestUser3/follow/')
        response = self.client.get('/follow/')
        self.assertContains(response, text = 'Test post')


    def test_no_news(self):
        self.client.login(username='TestUser2', password='321654')
        response = self.client.get('/follow/')
        self.assertNotContains(response, text = 'Test post')
    

    def test_comments(self):
        """Только авторизированный пользователь может комментировать посты."""
        self.client.login(username="TestUser", password="123456")
        post_id = self.post.pk
        self.client.post('/TestUser3/1/comment', {'text': 'Test comment'})
        response = self.client.get('/TestUser3/1/')
        self.assertEqual(response.status_code, 200)
    

    def test_no_comments(self):
        """Неавторизированный пользователь не может комментировать посты."""
        response = self.client.get('/TestUser3/1/comment')
        self.assertEquals(response.status_code, 301)
     