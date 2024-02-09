from django.contrib.auth.tokens import PasswordResetTokenGenerator


class ExpiringTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return str(user.pk) + str(timestamp) + str(login_timestamp)


account_activation_token = ExpiringTokenGenerator()
