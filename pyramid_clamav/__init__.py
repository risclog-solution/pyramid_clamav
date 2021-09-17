import json.decoder
import re
import urllib.error
import base64
import clamd
import logging
import sys
import time
from io import BytesIO
from pyramid.i18n import TranslationStringFactory, get_localizer
_ = TranslationStringFactory('pyramid_clamav')


clamlog = logging.getLogger(__name__)


def handle_virus(request, sig, key):
    localizer = get_localizer(request)
    log_message = 'Virus found: "{}"; Request key "{}"'.format(sig, key)
    clamlog.error(log_message)
    request.session.flash(
        localizer.translate(
            _('found-virus-user-message',
              default=('Virus found in file upload: ${sig}. '
                       'The file has been removed from the request.'),
              mapping={'sig': sig})),
        'error')
    if key in request.POST:
        del request.POST[key]
    return log_message


def is_base64(element):
    expression = "^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$"

    try:
        return bool(re.match(expression, element))
    except TypeError:
        return False


def check_json_data_for_virus(data, tween, request, key=None):
    if (isinstance(data, list)):
        for item in data:
            check_json_data_for_virus(item, tween, request)
    elif (isinstance(data, dict)):
        for key, value in data.items():
            check_json_data_for_virus(value, tween, request, key=key)
    else:
        if is_base64(data):
            file = BytesIO(base64.b64decode(data))
            message = tween._handle(request, key, file)
            if message:
                raise urllib.error.HTTPError(400, message, None, None, None)


class Tween(object):

    scanning = True

    def __init__(self, handler, config):
        self.handler = handler
        self.config = config
        clamd_debug = config.get('pyramid_clamav.debug', 'False')
        if clamd_debug.lower().strip() in ('false', '0', 'no'):
            clamd_debug = False
        if sys.platform == 'darwin':
            self.clamd = clamd.ClamdUnixSocket('/tmp/clamd.socket')
        else:
            self.clamd = clamd.ClamdUnixSocket()
        if clamd_debug:
            try:
                self.clamd.ping()
            except clamd.ConnectionError:
                self.scanning = False
        if not self.scanning:
            clamlog.warn('Virus scanning deactivated. (pyramid_clamav.debug '
                         'is true and clamav not properly configured!')
        else:
            clamlog.info('Found clamd and its responding. Virus scanning '
                         'activated.')

    def _check_file(self, request, key, file, checks=0):
        try:
            return self.clamd.instream(file)
        except (OSError, BrokenPipeError, clamd.ConnectionError):
            checks += 1
            if checks == 3:
                raise
            time.sleep(0.5)
            file.seek(0)
            return self._check_file(request, key, file, checks)

    def _handle(self, request, key, file):
        if not self.scanning:
            localizer = get_localizer(request)
            request.session.flash(
                localizer.translate(
                    _(
                        'clamav-not-configured-message',
                        default=(
                            'File upload found but clamav is not '
                            'configured.'
                        )
                    )
                ),
                'error'
            )
            clamlog.error(
                'File upload found but clamav is not configured.'
            )
            return
        try:
            result = self._check_file(request, key, file)
        except (
            OSError, BrokenPipeError, clamd.ConnectionError
        ) as e:
            clamlog.error(
                'Connection to ClamD was lost: {}'.format(str(e))
            )
            file.seek(0)
        else:
            if result and result.get('stream')[0] == 'FOUND':
                sig = result.get('stream')[1]
                return handle_virus(request, sig, key)
            else:
                file.seek(0)

    def __call__(self, request):
        if request.headers.get('Content-Type', '').startswith(
                'multipart/form-data'):
            for key in request.POST.keys():
                if hasattr(request.POST[key], 'file') and \
                       self.is_file_like(request.POST[key].file):
                    self._handle(request, key, request.POST[key].file)
        if request.headers.get('Content-Type', '') == 'application/json':
            try:
                request.json
            except json.decoder.JSONDecodeError:
                pass  # Broken json request, handle in application
            else:
                check_json_data_for_virus(request.json, self, request)
        return self.handler(request)

    def is_file_like(self, obj):
        return hasattr(obj, 'read') and hasattr(obj, 'seek')


def factory(handler, registry):
    return Tween(handler, registry.settings.copy())


def includeme(config):
    config.add_tween('pyramid_clamav.factory')
