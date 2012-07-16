from zope.interface import Interface, implements
from networkobjects import *
import json

class ILineSerializer(Interface):
	"""Classes implementing this must serialize data to string containing no newlines."""
	def serialize(self, obj):
		"""
		Return the serialized string of an object.
		Raises an InvalidSerializedDataException if the passed data is invalid.
		"""

	def deserialize(self, str):
		"""Return the object of a serialized string."""

class InvalidSerializedDataException(Exception):
	def __init__(self, serializer):
		self.serializerName = serializer.__class__.__name__

	def __str__(self):
		return "This string was not generated by this version of "\
		       + self.serializerName + ", or this serializer has a bug."

class JSONSerializer(object):
	implements(ILineSerializer)

	def __init__(self, serializeableObjectsModule):
		self._jsonEncoder = self._CustomEncoder()
		self.serializeableObjectsModule = serializeableObjectsModule

	def serialize(self, obj):
		return self._jsonEncoder.encode(obj)

	#TODO: Use more reflection and make (de)serialization automatic!
	def deserialize(self, string):
		try:
			data = json.loads(string)
		except ValueError:
			raise InvalidSerializedDataException(self)

		if not data.has_key('className'):
			raise InvalidSerializedDataException(self)

		class_ = getattr(self.serializeableObjectsModule, data['className'])
		if class_ is LoginRequest:
			return class_(
				data['firstName'],
				data['lastName'],
				data['password'],
				data['grid'])

		elif class_ is CreateUserRequest:
			return class_(
				data['firstName'],
				data['lastName'],
				data['password'],
				data['email'])

		else:
			return class_()

	class _CustomEncoder(json.JSONEncoder):
		def default(self, obj):
			# The decoder looks for the className to choose decoding scheme.
			data = {'className': obj.__class__.__name__}

			if isinstance(obj, LoginRequest):
				data['firstName'] = obj.firstName
				data['lastName'] = obj.lastName
				data['password'] = obj.password
				data['grid'] = obj.grid
				return data

			elif isinstance(obj, CreateUserRequest):
				data['firstName'] = obj.firstName
				data['lastName'] = obj.lastName
				data['password'] = obj.password
				data['email'] = obj.email
				return data
			
			else:
				return data
