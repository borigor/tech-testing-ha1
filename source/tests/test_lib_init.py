# coding: utf-8
import mock
import unittest
from lib import to_unicode, to_str, get_counters, check_for_meta, fix_market_url, prepare_url, get_redirect_history, \
    get_url, REDIRECT_HTTP, make_pycurl_request, REDIRECT_META


class InitLibTestCase(unittest.TestCase):
    def test_to_unicode(self):
        val = u"val"
        result = to_unicode(val)
        self.assertTrue(result, unicode)

    def test_to_unicode_else(self):
        val = "значение"
        result = to_unicode(val)
        self.assertTrue(result, unicode)

    def test_to_str(self):
        val = u"val"
        result = to_str(val)
        self.assertTrue(result, unicode)

    def test_to_str_else(self):
        val = "значение"
        result = to_str(val)
        self.assertTrue(result, unicode)

    def test_get_counters_match(self):
        content = 'http://google-analytics.com/ga.js'
        self.assertEquals(1, len(get_counters(content)))

    def test_get_counters_else(self):
        content = ''
        self.assertEquals(get_counters(content), [])

##########################################################################

    def test_check_for_meta_no_result(self):
        content = "content"
        url = "url"

        soup = mock.Mock()
        soup.find = mock.Mock(return_value=False)

        with mock.patch("lib.BeautifulSoup", mock.Mock(return_value=soup)):
            self.assertIsNone(check_for_meta(content, url))

    def test_check_for_meta_result_not_split(self):
        content = "content"
        url = "url"

        result = mock.MagicMock()
        result.attrs = {
            'content': "content",
            'http-equiv': "refresh"
        }

        soup = mock.Mock()
        soup.find = mock.Mock(return_value=result)

        with mock.patch("lib.BeautifulSoup", mock.Mock(return_value=soup)):
            with mock.patch("re.search", mock.Mock()) as mock_re_search:
                res = check_for_meta(content, url)

        self.assertIsNone(res)
        self.assertFalse(mock_re_search.called)

    def test_check_for_meta_result_split(self):
        content = "content"
        url = "url"

        result = mock.MagicMock()
        result.attrs = {
            'content': "wait;text",
            'http-equiv': "refresh"
        }

        soup = mock.Mock()
        soup.find = mock.Mock(return_value=result)
        re_search = mock.Mock()

        with mock.patch("lib.BeautifulSoup", mock.Mock(return_value=soup)):
            with mock.patch("re.search", re_search):
                res = check_for_meta(content, url)

        self.assertIsNone(res)
        assert re_search.call_count == 0

    def test_check_for_meta_result_m(self):
        content = "content"
        url = "url"

        result = mock.MagicMock()
        result.attrs = {
            'content': "wait;text",
            'http-equiv': "refresh"
        }

        soup = mock.Mock()
        soup.find = mock.Mock(return_value=result)
        m_mock = mock.MagicMock()
        re_search = mock.Mock(return_value=m_mock)

        with mock.patch("lib.BeautifulSoup", mock.Mock(return_value=soup)):
            with mock.patch("re.search", re_search):
                res = check_for_meta(content, url)

        self.assertIsNone(res)
        assert re_search.call_count == 0

#################################################################################################

    def test_fix_market_url(self):
        url = 'market://apps-url'
        return_url = 'http://play.google.com/store/apps/apps-url'
        self.assertEquals(return_url, fix_market_url(url))

    def test_fix_market_url_not_market(self):
        url = 'http://apps-url'
        self.assertEquals(url, fix_market_url(url))

    ##################################################

    def test_make_pycurl_request_redirect_url(self):
        url = u'http://url.ru'
        timeout = 30
        content = 'content'
        redirect_url = u'http://redirect-url.ru'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=redirect_url)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals(('', redirect_url), make_pycurl_request(url, timeout))

    def test_make_pycurl_request_redirect_url_useragent(self):
        url = u'http://url.ru'
        timeout = 30
        content = 'content'
        redirect_url = u'http://redirect-url.ru'
        useragent = 'useragent'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=redirect_url)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals(('', redirect_url), make_pycurl_request(url, timeout, useragent))

    def test_make_pycurl_request_none(self):
        url = u'http://url.ru'
        timeout = 30
        content = 'content'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=None)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals(('', None), make_pycurl_request(url, timeout))

    def test_make_pycurl_request_none_useragent(self):
        url = u'http://url.ru'
        timeout = 30
        content = 'content'
        useragent = 'useragent'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=None)
        with mock.patch('source.lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals(('', None), make_pycurl_request(url, timeout, useragent))

    ##################################################

    def test_get_url_wrong_url(self):
        """
        error in url
        """
        url = "wrong url"
        with mock.patch("source.lib.make_pycurl_request", mock.Mock(side_effect=ValueError('Value Error'))):
            self.assertEquals(get_url(url, timeout=1), (url, 'ERROR', None))


    ##################################################

    def test_get_redirect_history_ok_url(self):
        url = u'https://odnoklassniki.ru/'
        timeout = 10
        prepare_url = mock.Mock(return_value=url)

        with mock.patch('source.lib.prepare_url', prepare_url):
            history_types, history_urls, counters = get_redirect_history(url, timeout)

        self.assertEquals([], history_types)
        self.assertEquals([url], history_urls)
        self.assertEquals([], counters)

    def test_get_redirect_history_ok_url_mm(self):
        url = 'http://odnoklassniki.ru/'

        with mock.patch('source.lib.prepare_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_counters', mock.Mock()) as get_counters:
                get_redirect_history(url, 30)

        assert False == get_counters.called

    def test_get_redirect_history_for_mm(self):
        url = 'http://my.mail.ru/apps/'
        self.assertEqual(get_redirect_history(url, 10), ([], [url], []))

    def test_get_redirect_history_for_od(self):
        url = 'http://www.odnoklassniki.ru/someapp'
        self.assertEqual(get_redirect_history(url, 10), ([], [url], []))

    def test_get_regirect_history_repeat(self):
        url_example = 'http://example.com'
        url = ('http://test.org', REDIRECT_HTTP, None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertFalse(get_redirect_history(url_example, 10) == ([url[1], url[1]], [url_example, url[0], url[0]], []))

    def test_get_redirect_history_overlimit(self):
        url_example = 'http://example.com'
        url = ('http://test.org', REDIRECT_HTTP, None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertFalse(get_redirect_history(url_example, 10, 1) == ([url[1]], [url_example, url[0]], []))

    def test_get_redirect_no_redirect_url(self):
        url_example = 'http://example.com'
        url = (None, REDIRECT_HTTP, None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertEqual(get_redirect_history(url_example, 10), ([], [url_example], []))

    def test_get_redirect_error_redirect_type(self):
        url_example = 'http://example.com'
        url = ('http://test.org', 'ERROR', None)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            self.assertFalse(get_redirect_history(url_example, 10) == ([url[1]], [url_example, url[0]], []))

    def test_get_redirect_with_counter(self):
        url_example = 'http://example.com'
        content = 'Content'
        counter = 'counter'
        url = ('http://test.org', REDIRECT_HTTP, content)
        with mock.patch('source.lib.get_url', mock.Mock(return_value=url)):
            with mock.patch('source.lib.get_counters', mock.Mock(return_value='counter')):
                self.assertFalse(get_redirect_history(url_example, 10, 1) == ([url[1]], [url_example, url[0]], counter))

    #################################################

    def test_prepare_url_none(self):
        self.assertIsNone(prepare_url(None))

    def test_prepare_url(self):
        url = "url"
        with mock.patch('source.lib.urlparse', mock.Mock(return_value=[mock.MagicMock()] * 6)) as urlparse:
            with mock.patch('source.lib.quote', mock.Mock()) as quote:
                with mock.patch('source.lib.quote_plus', mock.Mock()) as quote_plus:
                    prepare_url(url)

        urlparse.assert_called_once()
        quote.assert_called_once()
        quote_plus.assert_called_once()
