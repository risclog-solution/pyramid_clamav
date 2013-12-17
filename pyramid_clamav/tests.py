#coding:utf8
from pyramid_clamav import Tween
import clamd
import mock
import os
import tempfile
import unittest


class FakeFileUpload(object):

    def __init__(self, content):
        _, tmp = tempfile.mkstemp()
        os.write(_, content)
        self.file = open(tmp, 'rw')


class FakeRequest(object):

    def __init__(self, ctype, post):
        self.headers = {'Content-Type': ctype}
        self.POST = post


def fake_handler(arg):
    pass


clean_post = dict(uploadedfile=FakeFileUpload('clean file'))
clean_request = FakeRequest('multipart/form-data', clean_post)

vir_post = dict(uploadedfile=FakeFileUpload(clamd.EICAR))
vir_request = FakeRequest('multipart/form-data', vir_post)


class TestClam(unittest.TestCase):

    def test_request_with_no_vir_goes_trough(self):
        with mock.patch('pyramid_clamav.tests.fake_handler') as handler,\
                mock.patch('pyramid_clamav.handle_virus') as virus:
            tween = Tween(fake_handler, {})
            tween(clean_request)
            virus.assert_not_called()
            fake_handler.assert_called_with(clean_request)

    def test_vir_is_found_in_req(self):
        with mock.patch('pyramid_clamav.tests.fake_handler') as handler,\
                mock.patch('pyramid_clamav.handle_virus') as virus:
            tween = Tween(fake_handler, {})
            tween(vir_request)
            virus.assert_called_with(vir_request, 
                                     u'Eicar-Test-Signature',
                                     'uploadedfile')
            fake_handler.assert_called_with(vir_request)
            assert vir_request.POST['uploadedfile'].file.read() == ''


