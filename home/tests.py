import ssl
from unittest.mock import patch

from django.core import mail
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from home import views
from home.models import Song, SortFilter, Raaga, God, ContactMessage


class RegistrationVerificationTests(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_registration_sends_verification_email_and_requires_activation(self):
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verify', mail.outbox[0].subject.lower())

        user = get_user_model().objects.get(username='newuser')
        self.assertFalse(user.is_active)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_user_can_activate_account_from_email_link(self):
        user = get_user_model().objects.create_user(
            username='verifyme',
            email='verifyme@example.com',
            password='StrongPass123!',
            is_active=False,
        )

        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = self.client.get(reverse('activate_account', args=[uid, token]))

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)


class SongReviewTests(TestCase):
    def setUp(self):
        self.sort_filter = SortFilter.objects.create(name='Bhajan', description='Devotional song')
        self.raaga = Raaga.objects.create(name='Kedar', description='Classical raga')
        self.god = God.objects.create(name='Sai Baba', description='Divine guide', image='default.png')
        self.song = Song.objects.create(
            name='Om Sai Ram',
            description='A devotional bhajan',
            Raaga=self.raaga,
            sort_filter=self.sort_filter,
            audio_file='media/songs/test.mp3',
            god=self.god,
            lyrics_pdf='lyrics/LYRIC_FILE_NOT_YET_UPLOADED.pdf',
        )
        self.user = get_user_model().objects.create_user(username='reviewer', email='reviewer@example.com', password='StrongPass123!')

    def test_user_can_submit_review_and_average_rating_updates(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('song-review', args=[self.song.pk]),
            {'rating': 5, 'comment': 'Beautiful bhajan!'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful bhajan!')
        self.assertEqual(self.song.reviews.count(), 1)
        self.assertEqual(self.song.average_rating(), 5.0)


class ContactFormTests(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_contact_form_sends_email_and_redirects(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'Website question',
                'message': 'I would like to ask a question about the site.',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you for reaching out')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Website question', mail.outbox[0].subject)
        self.assertEqual(1, ContactMessage.objects.count())

        saved_message = ContactMessage.objects.get(email='test@example.com')
        self.assertEqual(saved_message.subject, 'Website question')
        self.assertIn('ask a question', saved_message.message.lower())

    def test_contact_page_loads(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contact the team')

    @patch('home.views.send_mail', side_effect=ssl.SSLCertVerificationError('certificate verify failed'))
    def test_contact_post_survives_smtp_certificate_failures(self, mock_send_mail):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Factory User',
                'email': 'factory@example.com',
                'subject': 'Factory test',
                'message': 'This should still be saved even if SMTP fails.',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'saved')
        self.assertEqual(ContactMessage.objects.filter(email='factory@example.com').count(), 1)
        self.assertEqual(mock_send_mail.call_count, 1)

    def test_contact_post_works_when_module_has_a_view_named_all(self):
        request = RequestFactory().post(
            reverse('contact'),
            {
                'name': 'Factory User',
                'email': 'factory@example.com',
                'subject': 'Factory test',
                'message': 'This should work without shadowing errors.',
            },
        )
        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()
        setattr(request, '_messages', FallbackStorage(request))

        response = views.contact(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.filter(email='factory@example.com').count(), 1)


class SearchViewTests(TestCase):
    def test_search_page_works_without_results(self):
        response = self.client.get(reverse('search'), {'query': 'does not exist'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No songs matched that search')
