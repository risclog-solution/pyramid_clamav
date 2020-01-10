from __future__ import unicode_literals
import clamd
import logging
import sys
import time
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
    del request.POST[key]


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

    def _check_file(self, request, key, checks=0):
        try:
            return self.clamd.instream(request.POST[key].file)
        except (OSError, BrokenPipeError, clamd.ConnectionError):
            checks += 1
            if checks == 3:
                raise
            time.sleep(0.5)
            request.POST[key].file.seek(0)
            return self._check_file(request, key, checks)

    def __call__(self, request):
        if request.headers.get('Content-Type', '').startswith(
                'multipart/form-data'):
            for key in request.POST.keys():
                if hasattr(request.POST[key], 'file') and \
                       self.is_file_like(request.POST[key].file):
                    if not self.scanning:
                        localizer = get_localizer(request)
                        request.session.flash(
                            localizer.translate(
                                _('clamav-not-configured-message',
                                  default=(
                                      'File upload found but clamav is not '
                                      'configured.'
                                    )
                                  )
                                ), 'error')
                        clamlog.error('File upload found but '
                                      'clamav is not configured.')
                        continue
                    try:
                        result = self._check_file(request, key)
                    except (
                        OSError, BrokenPipeError, clamd.ConnectionError
                    ) as e:
                        clamlog.error(
                            'Connection to ClamD was lost: {}'.format(str(e))
                        )
                        request.POST[key].file.seek(0)
                    else:
                        if result and result.get('stream')[0] == 'FOUND':
                            sig = result.get('stream')[1]
                            handle_virus(request, sig, key)
                        else:
                            request.POST[key].file.seek(0)
        return self.handler(request)

    def is_file_like(self, obj):
        return hasattr(obj, 'read') and hasattr(obj, 'seek')


def factory(handler, registry):
    return Tween(handler, registry.settings.copy())


def includeme(config):
    config.add_tween('pyramid_clamav.factory')
