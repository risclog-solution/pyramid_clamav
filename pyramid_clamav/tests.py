# coding=utf8
from pyramid_clamav import Tween
from io import BytesIO
import clamd
import mock
import os
import tempfile
import unittest


class FakeFileUpload(object):

    def __init__(self, content):
        _, tmp = tempfile.mkstemp()
        os.write(_, content)
        self.file = open(tmp, 'rb')


class StringIOFileUpload(object):

    def __init__(self, content):
        self.file = BytesIO(content)


class FakeRequest(object):

    def __init__(self, ctype, post):
        self.headers = {'Content-Type': ctype}
        self.POST = post


def fake_handler(arg):
    pass


clean_post = dict(uploadedfile=FakeFileUpload(b'clean file'))
clean_request = FakeRequest('multipart/form-data', clean_post)


class TestClam(unittest.TestCase):

    def test_request_with_no_vir_goes_through(self):
        with mock.patch('pyramid_clamav.tests.fake_handler') as fake_handler,\
                mock.patch('pyramid_clamav.handle_virus') as virus:
            tween = Tween(fake_handler, {})
            tween(clean_request)
            virus.assert_not_called()
            fake_handler.assert_called_with(clean_request)

    def test_vir_is_found_in_req(self):
        self.assert_virus_in_file_like_upload(FakeFileUpload(clamd.EICAR))

    def test_vir_is_found_in_req_with_stringio(self):
        self.assert_virus_in_file_like_upload(StringIOFileUpload(clamd.EICAR))

    def assert_virus_in_file_like_upload(self, file_like):
        post = dict(uploadedfile=file_like)
        request = FakeRequest('multipart/form-data', post)

        with mock.patch('pyramid_clamav.tests.fake_handler'), \
                mock.patch('pyramid_clamav.handle_virus') as virus:
            tween = Tween(fake_handler, {})
            tween(request)
            virus.assert_called_with(request,
                                     'Eicar-Test-Signature',
                                     'uploadedfile')
            fake_handler.assert_called_with(request)
            assert request.POST['uploadedfile'].file.read() == b''

    def test_no_failure_if_clamav_is_busy(self):
        with mock.patch('clamd.ClamdUnixSocket.instream') as instream:
            instream.side_effect = OSError('I am busy')
            tween = Tween(fake_handler, {})
            tween(clean_request)
