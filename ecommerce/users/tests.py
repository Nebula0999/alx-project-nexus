from django.test import TestCase
from django.contrib.auth import get_user_model
from .serializers import UserSerializer


class UserModelCompatTests(TestCase):
	def test_user_has_auth_properties(self):
		User = get_user_model()
		user = User.objects.create(username='tester', email='t@example.com', first_name='T', last_name='User', password='pw')
		self.assertFalse(user.is_anonymous)
		self.assertTrue(user.is_authenticated)


class UserSerializerTests(TestCase):
	def test_serialize_and_create_user(self):
		User = get_user_model()
		data = {
			'username': 'tester',
			'email': 'tester@example.com',
			'first_name': 'Test',
			'last_name': 'User',
			'password': 'strongpassword'
		}
		serializer = UserSerializer(data=data)
		self.assertTrue(serializer.is_valid(), serializer.errors)
		user = serializer.save()
		self.assertEqual(user.username, data['username'])
		self.assertNotEqual(user.password, data['password'])  # should be hashed
