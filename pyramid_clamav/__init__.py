import clamd
import logging
import os
import sys
from pyramid.i18n import TranslationStringFactory, get_localizer
_ = TranslationStringFactory('pyramid_clamav')


clamlog = logging.getLogger(__name__)


if sys.platform == 'darwin':
    CLAMD_DEFAULT = '/tmp/clamd.socket'
else:
    CLAMD_DEFAULT = '/var/run/clamav/clamd.sock'


def handle_virus(request, sig, key):
    localizer = get_localizer(request)
    log_message = u'Virus found: "{}"; Request key "{}"'.format(sig, key)
    clamlog.error(log_message)
    request.session.flash(_('found-virus-user-message',
        default=u'Virus found in file upload: ${sig}. '
            u'The file has been removed from the request.',
        mapping={'sig': sig}), 'error')
    del request.POST[key]


class Tween(object):

    scanning = True

    def __init__(self, handler, config):
        self.handler = handler
        clamd_debug = config.get('pyramid_clamav.debug', 'False')
        if clamd_debug.lower().strip() in ('false', '0', 'no'):
            clamd_debug = False
        clamd_socket_location = config.get(
            'pyramid_clamav.socket', CLAMD_DEFAULT)
        if not os.path.exists(clamd_socket_location) and clamd_debug:
            self.scanning = False
        self.clamd = clamd.ClamdUnixSocket(
            clamd_socket_location)
        if clamd_debug:
            try:
                self.clamd.ping()
            except clamd.ConnectionError:
                self.scanning = False
        if not self.scanning:
            clamlog.warn('Virus scanning deactivated. (pyramid_clamav.debug '
                         'is true and clamav not properly configured!')

    def __call__(self, request):
        if request.headers.get('Content-Type', '').startswith(
                'multipart/form-data'):
            for key in request.POST.keys():
                if hasattr(request.POST[key], 'file') and \
                       self.is_file_like(request.POST[key].file):
                    if not self.scanning:
                        request.session.flash(
                            _('clamav-not-configured-message',
                              default=u'File upload found but clamav is not '
                              u'configured.'), 'error')
                        clamlog.error('File upload found but '
                                      'clamav is not configured.')
                        continue
                    result = self.clamd.instream(request.POST[key].file)
                    if result.get('stream')[0] == u'FOUND':
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
