from django.shortcuts import render, redirect
from .credentials import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
from rest_framework.views import APIView
from requests import Request, post
from rest_framework import status
from rest_framework.response import Response
from .util import *
from api.models import Room
from .models import Votes


class AuthURL(APIView):
    def get(self, request, format=None):
        scopes = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
        url = Request('GET', 'https://accounts.spotify.com/authorize', params={
            "scope": scopes,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID
        }).prepare().url
        return Response({'url': url}, status=status.HTTP_200_OK)


def spotify_callback(request, format=None):
    code = request.GET.get('code')
    error = request.GET.get('error')

    response = post('https://accounts.spotify.com/api/token', data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).json()

    access_token = response.get('access_token')
    token_type = response.get('token_type')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    error = response.get('error')

    if not request.session.exists(request.session.session_key):
        request.session.create()

    update_or_create_user_tokens(
        request.session.session_key, access_token, token_type, refresh_token, expires_in)

    return redirect("frontend:")


class IsAuthenticated(APIView):
    def get(self, request, format=None):
        is_authenticated = is_spotify_authenticated(
            self.request.session.session_key)
        return Response({"status": is_authenticated}, status=status.HTTP_200_OK)


class CurrentSong(APIView):
    def get(self, request, format=None):
        room_code = self.request.session.get("room_code")
        queryset = Room.objects.filter(code=room_code)
        if queryset.exists():
            room = queryset[0]
            host = room.host
            endpoint = "player/currently-playing"
            response = execute_spotify_api_request(host, endpoint)

            if "error" in response or "item" not in response:
                return Response({}, status=status.HTTP_204_NO_CONTENT)

            item = response.get("item")
            duration = item.get("duration_ms")
            progress = response.get("progress_ms")
            album_cover = item.get("album").get("images")[0].get("url")
            is_playing = response.get("is_playing")
            song_id = item.get("id")

            artists_string = ""
            for i, artist in enumerate(item.get("artists")):
                if i > 0:
                    artists_string += ", "
                name = artist.get("name")
                artists_string += name
            votes_number = len(Votes.objects.filter(
                room=room, song_id=song_id))

            song = {
                "title": item.get("name"),
                "artists": artists_string,
                "duration": duration,
                "time": progress,
                "img_url": album_cover,
                "is_playing": is_playing,
                "votes": votes_number,
                "votes_needed": room.votes_to_skip,
                "id": song_id,
            }

            self.update_room_song(room, song_id)

            return Response(song, status=status.HTTP_200_OK)
        return Response({"BadRequest": "No room."}, status=status.HTTP_404_NOT_FOUND)

    def update_room_song(self, room, song_id):
        current_song = room.current_song

        if current_song != song_id:
            room.current_song = song_id
            room.save(update_fields=["current_song"])
            votes = Votes.objects.filter(room=room).delete()


class PauseSong(APIView):
    def put(self, request, format=None):
        room_code = self.request.session.get("room_code")
        room = Room.objects.filter(code=room_code)[0]
        if self.request.session.session_key == room.host or room.guest_can_pause:
            pause_song(room.host)
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        return Response({}, status=status.HTTP_403_FORBIDDEN)


class PlaySong(APIView):
    def put(self, request, format=None):
        room_code = self.request.session.get("room_code")
        room = Room.objects.filter(code=room_code)[0]
        if self.request.session.session_key == room.host or room.guest_can_pause:
            play_song(room.host)
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        return Response({}, status=status.HTTP_403_FORBIDDEN)


class SkipSong(APIView):
    # May be some edge cases that are not covered by this code.
    def post(self, request, format=None):
        room_code = self.request.session.get("room_code")
        room = Room.objects.filter(code=room_code)[0]
        votes = Votes.objects.filter(room=room, song_id=room.current_song)
        user_voted = Votes.objects.filter(
            user=self.request.session.session_key, room=room, song_id=room.current_song).exists()
        votes_needed = room.votes_to_skip
        if not user_voted:
            if self.request.session.session_key == room.host or len(votes) + 1 >= votes_needed:
                votes.delete()
                skip_song(room.host)
            else:
                vote = Votes(user=self.request.session.session_key,
                             room=room, song_id=room.current_song)
                vote.save()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
