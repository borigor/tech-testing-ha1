# coding: utf-8
import mock
import unittest
import pycurl
from lib import to_unicode, to_str, get_counters, check_for_meta, fix_market_url, prepare_url, get_redirect_history, \
    get_url, make_pycurl_request


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

    def test_get_counters(self):
        content = 'http://google-analytics.com/ga.js'
        self.assertEquals(1, len(get_counters(content)))

    def test_get_counters_else(self):
        content = ''
        self.assertEquals(get_counters(content), [])

    ############################################################

    def test_check_for_meta_no_result(self):
        content = "content"
        url = "url"

        soup = mock.Mock()
        soup.find = mock.Mock(return_value=False)

        with mock.patch("lib.BeautifulSoup", mock.Mock(return_value=soup)):
            self.assertIsNone(check_for_meta(content, url))

    def test_check_for_meta_result_no_attrs(self):
        content = "content"
        url = "url"

        result = mock.MagicMock()
        result.attrs = {
            'content': "content",
        }

        soup = mock.Mock()
        soup.find = mock.Mock(return_value=result)

        with mock.patch("lib.BeautifulSoup", mock.Mock(return_value=soup)):
            with mock.patch("re.search", mock.Mock()) as mock_re_search:
                res = check_for_meta(content, url)

        self.assertIsNone(res)
        self.assertFalse(mock_re_search.called)

    def test_check_for_meta_result_wrong_value(self):
        content = "content"
        url = "url"

        result = mock.MagicMock()
        result.attrs = {
            'content': "content",
            'http-equiv': "Refresh"
        }

        soup = mock.Mock()
        soup.find = mock.Mock(return_value=result)

        with mock.patch("lib.BeautifulSoup", mock.Mock(return_value=soup)):
            with mock.patch("re.search", mock.Mock()) as mock_re_search:
                res = check_for_meta(content, url)

        self.assertIsNone(res)
        self.assertFalse(mock_re_search.called)

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

    #####################################################################

    def test_fix_market_url(self):
        url = "market://apps-url"
        return_url = "http://play.google.com/store/apps/apps-url"
        self.assertEquals(return_url, fix_market_url(url))

    def test_fix_market_url_not_market(self):
        url = "http://apps-url"
        self.assertEquals(url, fix_market_url(url))

    #####################################################################

    def test_make_pycurl_request_redirect_url(self):
        url = u'http://url.ru'
        timeout = 5
        content = 'content'
        redirect_url = u'http://redirect-url.ru'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=redirect_url)
        with mock.patch('lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals((content, redirect_url), make_pycurl_request(url, timeout))

    def test_make_pycurl_request_none(self):
        url = u'http://url.ru'
        timeout = 5
        content = 'content'
        buff = mock.MagicMock()
        buff.getvalue = mock.Mock(return_value=content)
        curl = mock.MagicMock()
        curl.setopt = mock.Mock()
        curl.perform = mock.Mock()
        curl.getinfo = mock.Mock(return_value=None)
        with mock.patch('lib.StringIO', mock.Mock(return_value=buff)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=curl)):
                self.assertEquals((content, None), make_pycurl_request(url, timeout))

    #####################################################################

    def test_get_url_meta(self):
        content = 'content'
        new_redirect = None
        new_redirect_meta = 'new_red_meta'
        url_test = 'url_test'
        timeout_test = 10
        REDIRECT_META = 'meta_tag'

        mock_make_pycurl = mock.Mock(return_value=(content, new_redirect))
        mock_check_for_meta = mock.Mock(return_value=new_redirect_meta)
        with mock.patch('lib.make_pycurl_request', mock_make_pycurl):
            with mock.patch('lib.check_for_meta', mock_check_for_meta):
                with mock.patch('lib.prepare_url', mock.Mock(return_value=new_redirect_meta)):
                    url, red, con = get_url(url_test, timeout_test)

        mock_make_pycurl.assert_called_once_with(url_test, timeout_test, None)
        self.assertEqual(new_redirect_meta, url)
        self.assertEqual(REDIRECT_META, red)
        self.assertEqual(content, con)

    def test_get_url_http(self):
        content = 'content'
        new_redirect = 'http://test.com'
        url_test = 'url_test'
        timeout_test = 10
        REDIRECT_HTTP = 'http_status'

        mock_make_pycurl = mock.Mock(return_value=(content, new_redirect))
        mock_check_for_meta = mock.Mock(return_value=new_redirect)
        with mock.patch('lib.make_pycurl_request', mock_make_pycurl):
            with mock.patch('lib.check_for_meta', mock_check_for_meta):
                with mock.patch('lib.prepare_url', mock.Mock(return_value=new_redirect)):
                    url, red, con = get_url(url_test, timeout_test)

        mock_make_pycurl.assert_called_once_with(url_test, timeout_test, None)
        self.assertEqual(new_redirect, url)
        self.assertEqual(REDIRECT_HTTP, red)
        self.assertEqual(content, con)

    def test_get_url_none(self):
        content = 'test'
        new_redirect = 'http://www.odnoklassniki.ru/st.redirect/'
        url_test = 'url_test'
        timeout_test = 400

        mock_make_pycurl = mock.Mock(return_value=(content, new_redirect))

        with mock.patch('lib.make_pycurl_request', mock_make_pycurl):
            with mock.patch('lib.prepare_url', mock.Mock(return_value=None)):
                url, red, con = get_url(url_test, timeout_test)

        mock_make_pycurl.assert_called_once_with(url_test, timeout_test, None)
        self.assertEqual(None, url)
        self.assertEqual(None, red)
        self.assertEqual(content, con)

    def test_get_url_market(self):
        content = 'test'
        new_redirect = 'market://www.test/'
        return_fix_market = 'http://play.google.com/store/apps/www.test/'
        url_test = 'url_test'
        timeout_test = 400
        REDIRECT_HTTP = 'http_status'

        mock_make_pycurl = mock.Mock(return_value=(content, new_redirect))
        mock_fix_market_url = mock.Mock(return_value=return_fix_market)
        with mock.patch('lib.make_pycurl_request', mock_make_pycurl):
            with mock.patch('lib.fix_market_url', mock_fix_market_url):
                with mock.patch('lib.prepare_url', mock.Mock(return_value=return_fix_market)):
                    url, red, con = get_url(url_test, timeout_test)

        mock_make_pycurl.assert_called_once_with(url_test, timeout_test, None)
        mock_fix_market_url.assert_called_once_with(new_redirect)
        self.assertEqual(return_fix_market, url)
        self.assertEqual(REDIRECT_HTTP, red)
        self.assertEqual(content, con)

    def test_get_url_error(self):
        url_test = 'url_test'
        timeout_test = 400

        mock_make_pycurl = mock.Mock(side_effect=pycurl.error)
        with mock.patch('lib.make_pycurl_request', mock_make_pycurl):
            url, red, con = get_url(url_test, timeout_test)

        mock_make_pycurl.assert_called_once_with(url_test, timeout_test, None)
        self.assertEqual(url_test, url)
        self.assertEqual('ERROR', red)
        self.assertEqual(None, con)

    ####################################################################

    def test_get_redirect_history_empty(self):
        url_test = 'http://test.com'
        timeout_test = 777
        mock_re_match = mock.Mock(return_value=True)
        with mock.patch('lib.prepare_url', mock.Mock(side_effect=prepare_url)):
            with mock.patch('re.match', mock_re_match):
                history_type, history_url, counters = get_redirect_history(url_test, timeout_test)

        self.assertEqual([], history_type)
        self.assertEqual([url_test], history_url)
        self.assertEqual([], counters)

    def test_get_redirect_history_not_redirect_url(self):
        url_test = 'http://test.com'
        timeout_test = 777
        return_redirect_url = None
        return_content = None
        return_redirect_type = 'http_status'

        mock_re_match = mock.Mock(return_value=False)
        mock_get_url = mock.Mock(return_value=(return_redirect_url, return_redirect_type, return_content))
        with mock.patch('lib.prepare_url', mock.Mock(side_effect=prepare_url)):
            with mock.patch('re.match', mock_re_match):
                with mock.patch('lib.get_url', mock_get_url):
                    history_type, history_urls, counters = get_redirect_history(url_test, timeout_test)

        mock_get_url.assert_called_once_with(url=url_test, timeout=timeout_test, user_agent=None)
        self.assertEqual([], history_type)
        self.assertEqual([url_test], history_urls)
        self.assertEqual([], counters)

    def test_get_redirect_history_error(self):
        url_test = 'http://test.com'
        timeout_test = 777
        return_redirect_url = 'http://redirect/test.com'
        return_content = None
        return_redirect_type = 'ERROR'

        re_match_mock = mock.Mock(return_value=False)
        get_url_mock = mock.Mock(return_value=(return_redirect_url, return_redirect_type, return_content))
        with mock.patch('lib.prepare_url', mock.Mock(side_effect=prepare_url)):
            with mock.patch('re.match', re_match_mock):
                with mock.patch('lib.get_url', get_url_mock):
                    history_type, history_urls, counters = get_redirect_history(url_test, timeout_test)

        get_url_mock.assert_called_once_with(url=url_test, timeout=timeout_test, user_agent=None)
        self.assertEqual([return_redirect_type], history_type)
        self.assertEqual([url_test, return_redirect_url], history_urls)
        self.assertEqual([], counters)

    def test_get_redirect_history(self):
        url_test = 'http://test.com'
        timeout_test = 777
        max_redirects_test = 1
        return_redirect_url = 'http://redirect/test.com'
        return_content = None
        return_redirect_type = 'meta_tag'

        re_match_mock = mock.Mock(return_value=False)
        get_url_mock = mock.Mock(return_value=(return_redirect_url, return_redirect_type, return_content))
        with mock.patch('lib.prepare_url', mock.Mock(side_effect=prepare_url)):
            with mock.patch('re.match', re_match_mock):
                with mock.patch('lib.get_url', get_url_mock):
                    history_type, history_urls, counters = get_redirect_history(url_test, timeout_test, max_redirects_test)

        get_url_mock.assert_called_with(url=url_test, timeout=timeout_test, user_agent=None)
        self.assertEqual([return_redirect_type], history_type)
        self.assertEqual([url_test, return_redirect_url], history_urls)
        self.assertEqual([], counters)

    #################################################################################################

    def test_prepare_url_none(self):
        self.assertIsNone(prepare_url(None))

    def test_prepare_url(self):
        url = "url"
        with mock.patch('lib.urlparse', mock.Mock(return_value=[mock.MagicMock()] * 6)) as urlparse:
            with mock.patch('lib.quote', mock.Mock()) as quote:
                with mock.patch('lib.quote_plus', mock.Mock()) as quote_plus:
                    prepare_url(url)

        urlparse.assert_called_once()
        quote.assert_called_once()
        quote_plus.assert_called_once()

    def test_prepare_url_exception(self):
        netlock = mock.Mock()
        netlock.encode = mock.Mock(side_effect=UnicodeError)
        with mock.patch('lib.urlparse', mock.Mock(return_value=('scheme', netlock, 'path', 'qs', 'anchor', 'fragments'))):
            with mock.patch('lib.urlunparse', mock.Mock()) as urlunparse:
                prepare_url('url')
        self.assertTrue(urlunparse.called)
