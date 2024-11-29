from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        # Retrieve the token using the key
        model = self.get_model()
        try:
            token = model.objects.get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        expiration_time = timedelta(seconds=getattr(settings, 'TOKEN_EXPIRATION_TIME', 60))  

        # Check if the token has expired
        if timezone.now() - token.created > expiration_time:
            raise AuthenticationFailed('Access token has expired. Please log in again.')

        return (token.user, token)
