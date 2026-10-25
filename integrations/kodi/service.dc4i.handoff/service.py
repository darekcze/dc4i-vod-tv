# DC4I Kodi local title handoff. Host is strictly 127.0.0.1.
# Media source credentials are read from the user's existing XCUI configuration.
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, urlencode

import xbmc
import xbmcaddon
import xbmcgui
from catalog_search import find_matches

PORT = 18761
DATA_FILE = os.path.join(os.path.dirname(__file__), 'catalog.json')
try:
    with open(DATA_FILE, encoding='utf-8') as source:
        CATALOG = json.load(source)
except Exception:
    CATALOG = {'movie': {}, 'series': {}}


def request_to_action(data):
    if not isinstance(data, dict):
        return {'ok': False, 'error': 'invalid-input'}
    if data.get('action')=='search':
        title=data.get('title','')
        if not isinstance(title,str) or not (2 <= len(title.strip()) <= 120):
            return {'ok': False, 'error':'invalid-title'}
        matches=find_matches(CATALOG,title)
        if not matches:
            xbmcgui.Dialog().notification('DC4I VOD TV', 'Brak wyników w Twoim katalogu Kodi', xbmcgui.NOTIFICATION_INFO, 3500)
            return {'ok':True, 'action':'search-empty','matches':0}
        labels=[('Film: ' if m[0]=='movie' else 'Serial: ')+m[2] for m in matches]
        selection=xbmcgui.Dialog().select('Szukaj w Kodi: '+title[:62],labels,preselect=0)
        if selection<0:
            return {'ok':True,'action':'search-cancelled','matches':len(matches)}
        chosen=matches[selection]
        return request_to_action({'type':chosen[0],'tmdb':chosen[1],'title':chosen[2]})
    media_type = data.get('type')
    tmdb = str(data.get('tmdb', ''))
    title = data.get('title', '')
    if media_type not in ('movie', 'series') or not re.fullmatch('[0-9]{1,10}', tmdb):
        return {'ok': False, 'error': 'invalid-id'}
    if not isinstance(title, str) or len(title) > 180:
        return {'ok': False, 'error': 'invalid-title'}
    match = CATALOG.get(media_type, {}).get(tmdb)
    if not match:
        return {'ok': False, 'error': 'not-in-provider', 'matched': False}
    try:
        settings = xbmcaddon.Addon('plugin.video.iptvxc')
        host = settings.getSetting('DNS').rstrip('/')
        username = settings.getSetting('Username')
        password = settings.getSetting('Password')
        if not host.startswith(('http://', 'https://')) or not username or not password:
            return {'ok': False, 'error': 'xtream-not-configured'}
        stream_id = int(match[0])
        if media_type == 'movie':
            ext = match[1] if match[1] in ('mp4', 'mkv', 'ts', 'avi', 'mov') else 'mp4'
            uri = '%s/movie/%s/%s/%s.%s' % (host, quote(username, safe=''), quote(password, safe=''), stream_id, ext)
            xbmc.Player().play(uri)
            return {'ok': True, 'matched': True, 'action': 'play-movie', 'title': match[2]}
        url = host + '/player_api.php?' + urlencode({'username': username, 'password': password, 'action': 'get_series_info', 'series_id': stream_id})
        plugin_path = 'plugin://plugin.video.iptvxc/?' + urlencode({'url': url, 'mode': 19, 'name': match[1]})
        xbmc.executebuiltin('ActivateWindow(Videos,"' + plugin_path + '",return)')
        return {'ok': True, 'matched': True, 'action': 'open-series', 'title': match[1]}
    except Exception:
        return {'ok': False, 'error': 'player-failed'}


class Handoff(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Suppress URLs and sensitive requests in all logs.
        return

    def cors(self):
        origin = self.headers.get('Origin', '')
        if origin in ('null', 'file://') or origin.startswith('app://com.dc4i.vodtv'):
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def send(self, status, data):
        raw = json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.cors()
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send(200, {'ok': True})

    def do_GET(self):
        if self.path != '/status':
            self.send(404, {'ok': False})
        else:
            self.send(200, {'ok': True, 'service': 'DC4I Kodi Handoff', 'movies': len(CATALOG.get('movie', {})), 'series': len(CATALOG.get('series', {}))})

    def do_POST(self):
        if self.path != '/open':
            return self.send(404, {'ok': False})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 2 or size > 1024:
                return self.send(413, {'ok': False, 'error': 'bad-size'})
            data = json.loads(self.rfile.read(size))
            result = request_to_action(data)
            self.send(200, result)
        except Exception:
            self.send(400, {'ok': False, 'error': 'bad-payload'})


class ReusableServer(ThreadingHTTPServer):
    allow_reuse_address = True


def startup_handoff():
    """Read appManager params from the authorized Kodi process launch, never logs secrets."""
    try:
        # webOS passes one JSON argument to the Kodi native executable.
        # Native addon Python code runs in that SAME process on the TV.
        with open('/proc/self/cmdline', 'rb') as proc:
            cmdline = proc.read(16000)
        for item in cmdline.split(b'\x00'):
            if not item.strip().startswith(b'{'):
                continue
            try:
                params = json.loads(item.decode('utf-8')).get('parameters', {})
            except (UnicodeDecodeError, ValueError, AttributeError):
                continue
            data = params.get('dc4i') if isinstance(params, dict) else None
            if isinstance(data, dict) and (data.get('tmdb') is not None or data.get('action')=='search'):
                # Only accept data from Kodi's own launch contract.
                return data
    except (IOError, OSError, ValueError) as exc:
        xbmc.log('[DC4I] Native startup metadata unavailable', xbmc.LOGWARNING)
    return None


server = None
monitor = xbmc.Monitor()
try:
    server = ReusableServer(('127.0.0.1', PORT), Handoff)
    server.timeout = 0.5
    xbmc.log('[DC4I] Kodi title handoff ready on local loopback', xbmc.LOGINFO)
    # Kodi may not have a media window yet at the start of the Python service.
    pending = startup_handoff()
    started = __import__('time').monotonic()
    while not monitor.abortRequested():
        server.handle_request()
        if pending is not None and __import__('time').monotonic() - started >= 3.0:
            command = pending
            pending = None
            result = request_to_action(command)
            # Never log source URLs, provider credentials or untrusted payloads.
            xbmc.log('[DC4I] launch handoff: ' + str(result.get('action') or result.get('error')), xbmc.LOGINFO)
finally:
    if server is not None:
        server.server_close()