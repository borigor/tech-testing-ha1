import mock
import unittest
from lib import utils


class UtilsTestCase(unittest.TestCase):
    def test_daemonize(self):
        pid = 13
        with mock.patch("os.fork", mock.Mock(return_value=pid)) as mock_os_fork:
            with mock.patch("os._exit", mock.Mock()) as mock_os_exit:
                utils.daemonize()

        mock_os_fork.assert_called_once_with()
        mock_os_exit.assert_called_once_with(0)

    def test_daemonize_pid_zero(self):
        pid = 0
        with mock.patch("os.fork", mock.Mock(return_value=pid)) as mock_os_fork:
            with mock.patch("os.setsid", mock.Mock()) as mock_os_setsid:
                utils.daemonize()

        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count == 2)

    def test_daemonize_pid_zero_not_zero(self):
        pid = 13
        with mock.patch("os.fork", mock.Mock(side_effect=[0, pid])) as mock_os_fork:
            with mock.patch("os.setsid", mock.Mock()) as mock_os_setsid:
                with mock.patch("os._exit", mock.Mock()) as mock_os_exit:
                    utils.daemonize()

        mock_os_setsid.assert_called_once_with()
        mock_os_exit.assert_called_once_with(0)
        self.assertTrue(mock_os_fork.call_count == 2)

    def test_daemonize_oserror(self):
        with mock.patch("os.fork", mock.Mock(side_effect=OSError)) as mock_os_fork:
            self.assertRaises(Exception, utils.daemonize)

        mock_os_fork.assert_called_once_with()

    def test_daemonize_pid_zero_oserror(self):
        with mock.patch("os.fork", mock.Mock(side_effect=[0, OSError])) as mock_os_fork:
            with mock.patch("os.setsid", mock.Mock()) as mock_os_setsid:
                self.assertRaises(Exception, utils.daemonize)

        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count == 2)

    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_load_config_from_pyfile(self):
        result = utils.load_config_from_pyfile('source/tests/test_config.py')
        self.assertEqual(result.CONF_KEY, 1)
        self.assertEqual(result.CONF_KEY_1, 'value')
        self.assertFalse(hasattr(result, 'Conf_Key_2'))
        self.assertEqual(result.CONF_KEY_THREE, {
            'value_key_1': 'value_1',
            'value_key_2': 'value_2'
        })

    def test_parse_cmd_args(self):
        arg = mock.MagicMock()
        args = [arg, arg]
        app_descr = mock.MagicMock()
        parser = mock.Mock()
        with mock.patch("lib.utils.argparse.ArgumentParser", mock.Mock(return_value=parser)):
            utils.parse_cmd_args(args, app_descr)

        parser.parse_args.assert_called_once_with(args=args)

    def test_get_tube(self):
        host = "host"
        port = 0
        space = 0
        name = 'name'

        mock_queue = mock.MagicMock()
        mock_t_queue = mock.Mock(return_value=mock_queue)

        with mock.patch("lib.utils.tarantool_queue.Queue", mock_t_queue):
            utils.get_tube(host, port, space, name)

        mock_t_queue.assert_called_once_with(host=host, port=port, space=space)
        mock_queue.tube.assert_called_once_with(name)

    def test_spawn_workers(self):
        num = 13
        target = mock.Mock()
        args = ''
        parent_pid = 13

        mock_p = mock.MagicMock()
        mock_p.daemon = False
        mock_p.start = mock.Mock()

        mock_process = mock.Mock(return_value=mock_p)

        with mock.patch('lib.utils.Process', mock_process):
            utils.spawn_workers(num, target, args, parent_pid)

        assert mock_process.call_count == num
        self.assertTrue(mock_p.daemon)

    def test_network_status_ok(self):
        mock_check_url = mock.Mock()
        timeout = 0

        mock_urllib = mock.Mock(return_value=True)

        with mock.patch('urllib2.urlopen', mock_urllib):
            utils.check_network_status(mock_check_url, timeout)

        mock_urllib.assert_call_once_with(mock_check_url, timeout)

    def test_network_status_value_error(self):
        mock_check_url = mock.Mock()
        timeout = 113

        mock_urllib = mock.Mock(side_effect=ValueError())

        with mock.patch('urllib2.urlopen', mock_urllib):
            self.assertFalse(utils.check_network_status(mock_check_url, timeout))