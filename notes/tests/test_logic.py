from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from notes.forms import WARNING
from django.urls import reverse

from notes.models import Note


User = get_user_model()

INDEX = 1


class TestNoteCreation(TestCase):

    TEXT = 'Текст успеха'
    SLUG = 'test_success'
    TITLE = f'Заметка {INDEX}'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.url = reverse('notes:add', args=None)
        cls.url_success = reverse('notes:success', args=None)
        cls.form_data = {'title': cls.TITLE,
                         'text': cls.TEXT,
                         'slug': cls.SLUG}

    def test_user_cant_use_same_slug(self):
        Note.objects.create(title=self.TITLE,
                            text=self.TEXT,
                            author=self.author)
        tasks_count = Note.objects.count()
        same_note = {'title': self.TITLE,
                     'text': self.TEXT,
                     'author': self.author}
        slug = slugify(same_note['title'])[:100]
        response = self.auth_client.post(self.url, data=same_note)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{slug}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, tasks_count)

    def test_user_successfully_create_note(self):
        notes_count = Note.objects.count()
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.url_success)
        notes_count_new = Note.objects.count()
        self.assertEqual(notes_count_new, notes_count + 1)
        note = Note.objects.get(slug=self.SLUG)
        self.assertEqual(note.text, self.TEXT)
        self.assertEqual(note.title, self.TITLE)
        self.assertEqual(note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        notes_count = Note.objects.count()
        self.client.post(self.url, data=self.form_data)
        notes_count_new = Note.objects.count()
        self.assertEqual(notes_count_new, notes_count)


class TestCommentEditDelete(TestCase):
    TEXT = 'Текст успеха'
    NEW_TEXT = 'Новый текст успеха'
    SLUG = 'test_success'
    TITLE = f'Заметка {INDEX+1}'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(title=cls.TITLE,
                                       text=cls.TEXT,
                                       author=cls.author)
        cls.note_url_success = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {'title': cls.TITLE,
                         'text': cls.NEW_TEXT,
                         'slug': cls.SLUG}

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.note_url_success)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_comment(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.note_url_success)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.TEXT)
