import sys
import logging
import clamd
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

    def __init__(self, handler, config):
        self.handler = handler
        clamd_socket_location = config.get('clamd.socket', CLAMD_DEFAULT)
        self.clamd = clamd.ClamdUnixSocket(
            clamd_socket_location)

    def __call__(self, request):
        if request.headers.get('Content-Type', '').startswith(
                'multipart/form-data'):
            for key in request.POST.keys():
                if hasattr(request.POST[key], 'file') and \
                       type(request.POST[key].file) is file:
                    result = self.clamd.instream(request.POST[key].file)
                    if result.get('stream')[0] == u'FOUND':
                        sig = result.get('stream')[1]
                        handle_virus(request, sig, key)
                    else:
                        request.POST[key].file.seek(0)
        return self.handler(request)


def factory(handler, registry):
    return Tween(handler, registry.settings.copy())


def includeme(config):
    config.add_tween('pyramid_clamav.factory')
