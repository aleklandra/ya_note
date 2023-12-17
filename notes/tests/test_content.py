from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Левый Пользователь')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       slug='test',
                                       author=cls.author)

    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        urls = (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:detail', (self.note.slug,))
        )
        for name, arg in urls:
            with self.subTest(name=name):
                url = reverse(name, args=arg)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_user_cant_see_note_another_user(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND)
        )
        url = reverse('notes:detail', args=(self.note.slug,))
        for user, status in users_statuses:
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status)
