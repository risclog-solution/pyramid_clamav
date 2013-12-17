#coding:utf8

import unittest
from pyramid_clamav import Tween
import mock


class FakeFileUpload(object):

    def __init__(self, content):
        self.file = tempfile.mkstemp()
        self.file.write(content)
        self.file.seek(0)


class FakeRequest(object):

    headers = {}
    POST = {}
    session = object()


def fake_handler(arg):
    pass

clean_request = FakeRequest()
clean_request.headers['Content-Type'] = 'multipart/form-data'
clean_request.POST['uploadedfile'] = FakeFileUpload('clean file')

vir_request = FakeRequest()
vir_request.headers['Content-Type'] = 'multipart/form-data'
vir_request.POST['uploadedfile'] = FakeFileUpload(clamd.EICAR)


class TestClam(unittest.TestCase):

    def test_request_with_no_vir_goes_trough(self):
        tween = Tween(fake_handler, mock.sentinel.config)
        with mock.patch('FakeRequest.session.flash') as flash\
                mock.patch('fake_handler') as handler:
            tween(clean_request)
            flash.assert_not_called()
            fake_handler.assert_called_with(clean_request)

    def test_vir_is_found_in_req(self):
        tween = Tween(fake_handler, mock.sentinel.config)
        with mock.patch('FakeRequest.session.flash') as flash\
                mock.patch('fake_handler') as handler:
            tween(vir_request)
            flash.assert_called_with('asdf')
            fake_handler.assert_called_with(clean_request)


