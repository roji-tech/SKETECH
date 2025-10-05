from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


from api.serializers import SchoolSerializer
from main.tenancy.threadlocals import get_current_school


class LogoutView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_200_OK)
        except (ObjectDoesNotExist, TokenError):
            return Response(status=status.HTTP_400_BAD_REQUEST)


@permission_classes([AllowAny])
@api_view(['GET'])
def get_school_info(request):
    try:
        # Attempt to retrieve the school from the request
        school = get_current_school()
        if not school:
            raise NotFound("School not found or unauthorized access.")

        print("School:", school)

        # Serialize the school data
        serializer = SchoolSerializer(school)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except NotFound as e:
        # Handle cases where the school is not found
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        # Generic exception handler for unexpected errors
        print("An unexpected error occurred:", e)
        return Response(
            {"error": "An unexpected error occurred. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
