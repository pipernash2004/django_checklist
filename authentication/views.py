from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)
from .models import CustomUser


class RegisterView(APIView):
    """Register a new user.

    POST: Accepts registration data, creates a CustomUser, and returns
    a token and serialized user data. Open to unauthenticated clients.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    'message': 'User registered successfully',
                    'user': UserSerializer(user).data,
                    'token': token.key,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Authenticate a user and return a token.

    POST: Validates credentials using UserLoginSerializer and returns
    a token for API authentication.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'token': token.key,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Log out the authenticated user by deleting their token.

    POST: Deletes the Token instance tied to the request.user. Requires
    authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # If the user has an auth token, delete it to invalidate further
        # token-based requests from that client.
        try:
            request.user.auth_token.delete()
        except Exception:
            # If no token exists, ignore — logout is idempotent.
            pass
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class UserProfileView(RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile.

    GET: Return serialized user data for the current user.
    PUT/PATCH: Update fields on the current user's profile (partial
    updates supported via PATCH). Uses `UserSerializer`.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Always return the current authenticated user as the object to
        # retrieve or update; this prevents exposing other user records.
        return self.request.user
