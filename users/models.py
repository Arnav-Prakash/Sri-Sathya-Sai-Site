from django.conf import settings
from django.db import models


class AdminProfile(models.Model):
	SIMPLE = 'simple'
	DEVELOPER = 'developer'
	INTERFACE_MODES = (
		(SIMPLE, 'Simple workspace'),
		(DEVELOPER, 'Developer workspace'),
	)

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_profile')
	interface_mode = models.CharField(max_length=20, choices=INTERFACE_MODES, default=SIMPLE)
	profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

	def __str__(self):
		return f'{self.user.username} admin preferences'
