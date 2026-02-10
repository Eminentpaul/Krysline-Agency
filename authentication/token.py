from django.contrib.auth.tokens import PasswordResetTokenGenerator

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Token remains valid as long as 'is_active' status hasn't changed
        return str(user.pk) + str(timestamp) + str(user.is_active)

email_verification_token = EmailVerificationTokenGenerator()
# print('Email Verification:', email_verification_token)