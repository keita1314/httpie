import os

import pytest

from httpie.input import ParseError
from utils import TestEnvironment, http, HTTP_OK
from fixtures import FILE_PATH_ARG, FILE_PATH, FILE_CONTENT


class TestMultipartFormDataFileUpload:

    def test_non_existent_file_raises_parse_error(self, httpbin):
        with pytest.raises(ParseError):
            http('--form',
                 'POST', httpbin.url + '/post', 'foo@/__does_not_exist__')

    def test_upload_ok(self, httpbin):
        r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                 'test-file@%s' % FILE_PATH_ARG, 'foo=bar')
        assert HTTP_OK in r
        assert 'Content-Disposition: form-data; name="foo"' in r
        assert 'Content-Disposition: form-data; name="test-file";' \
               ' filename="%s"' % os.path.basename(FILE_PATH) in r
        assert FILE_CONTENT in r
        assert '"foo": "bar"' in r

    def test_upload_multiple_fields_with_the_same_name(self, httpbin):
        r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                 'test-file@%s' % FILE_PATH_ARG,
                 'test-file@%s' % FILE_PATH_ARG)
        assert HTTP_OK in r
        assert r.count('Content-Disposition: form-data; name="test-file";'
               ' filename="%s"' % os.path.basename(FILE_PATH)) == 2
        # Should be 4, but is 3 because httpbin
        # doesn't seem to support filed field lists
        assert r.count(FILE_CONTENT) in [3, 4]


class TestRequestBodyFromFilePath:
    """
    `http URL @file'

    """

    def test_request_body_from_file_by_path(self, httpbin):
        r = http('--verbose',
                 'POST', httpbin.url + '/post', '@' + FILE_PATH_ARG)
        assert HTTP_OK in r
        assert FILE_CONTENT in r, r
        assert '"Content-Type": "text/plain"' in r

    def test_request_body_from_file_by_path_with_explicit_content_type(
            self, httpbin):
        r = http('--verbose',
                 'POST', httpbin.url + '/post', '@' + FILE_PATH_ARG,
                 'Content-Type:text/plain; charset=utf8')
        assert HTTP_OK in r
        assert FILE_CONTENT in r
        assert 'Content-Type: text/plain; charset=utf8' in r

    def test_request_body_from_file_by_path_no_field_name_allowed(
            self, httpbin):
        env = TestEnvironment(stdin_isatty=True)
        r = http('POST', httpbin.url + '/post', 'field-name@' + FILE_PATH_ARG,
                 env=env, error_exit_ok=True)
        assert 'perhaps you meant --form?' in r.stderr

    def test_request_body_from_file_by_path_no_data_items_allowed(
            self, httpbin):
        env = TestEnvironment(stdin_isatty=False)
        r = http('POST', httpbin.url + '/post', '@' + FILE_PATH_ARG, 'foo=bar',
                 env=env, error_exit_ok=True)
        assert 'cannot be mixed' in r.stderr


class TestMultipartFormDataAnonymousFileUpload:
    """
    `date| http -f POST URL file@-'
    """

    def test_stdin_as_file_upload_ok(self, httpbin):
        with open(FILE_PATH, 'rb') as f:
            env = TestEnvironment(stdin=f, stdin_isatty=False)
            r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                     'test-file@-', 'foo=bar', env=env)
        assert HTTP_OK in r
        assert 'Content-Disposition: form-data; name="foo"' in r
        assert 'Content-Disposition: form-data; name="test-file";' \
               ' filename="-"' in r
        assert FILE_CONTENT in r
        assert '"foo": "bar"' in r

    def test_upload_multiple_fields_with_the_same_name(self, httpbin):
        with open(FILE_PATH, 'rb') as f:
            env = TestEnvironment(stdin=f, stdin_isatty=False)
            r = http('--form', '--verbose', 'POST', httpbin.url + '/post',
                     'test-file@-','test-file@-', env=env)
        assert HTTP_OK in r
        assert r.count('Content-Disposition: form-data; name="test-file";'
               ' filename="-"') == 2
        # doesn't seem to support filed field lists
        assert r.count(FILE_CONTENT) == 2

    def test_upload_anonymous_file_without_stdin(self, httpbin):
        r = http('POST', httpbin.url + '/post', 'test-file@-',
                 error_exit_ok=True)
        assert 'you need stdin when http -f post f@-' in r.stderr
