import mock
import unittest
import redirect_checker


def stop_loop(*args, **kwargs):
    redirect_checker.is_run = False


class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_loop_status_workers(self):
        pid = 13
        mock_os_getpid = mock.Mock(return_value=pid)

        mock_check_net_status = mock.Mock(return_value=True)

        config = mock.Mock()
        config.WORKER_POOL_SIZE = 100
        config.SLEEP = 1
        config.CHECK_URL = 'CHECK_URL'
        config.HTTP_TIMEOUT = 100

        child = mock.MagicMock()
        active_children = [child, child]
        mock_active_children = mock.Mock(return_value=active_children)

        mock_spawn_workers = mock.Mock()

        mock_sleep = mock.Mock(side_effect=stop_loop)

        with mock.patch("os.getpid", mock_os_getpid):
            with mock.patch("redirect_checker.check_network_status", mock_check_net_status):
                with mock.patch("redirect_checker.active_children", mock_active_children):
                    with mock.patch("redirect_checker.spawn_workers", mock_spawn_workers):
                        with mock.patch("redirect_checker.sleep", mock_sleep):
                            redirect_checker.main_loop(config=config)

        mock_sleep.assert_called_once_with(config.SLEEP)
        assert mock_spawn_workers.call_count == 1

        redirect_checker.is_run = True

    def test_main_loop_status_no_workers(self):
        pid = 13
        mock_os_getpid = mock.Mock(return_value=pid)

        mock_check_net_status = mock.Mock(return_value=True)

        config = mock.Mock()
        config.WORKER_POOL_SIZE = 2
        config.SLEEP = 1
        config.CHECK_URL = 'CHECK_URL'
        config.HTTP_TIMEOUT = 100

        child = mock.MagicMock()
        active_children = [child, child]
        mock_active_children = mock.Mock(return_value=active_children)

        mock_spawn_workers = mock.Mock()

        mock_sleep = mock.Mock(side_effect=stop_loop)

        with mock.patch("os.getpid", mock_os_getpid):
            with mock.patch("redirect_checker.check_network_status", mock_check_net_status):
                with mock.patch("redirect_checker.active_children", mock_active_children):
                    with mock.patch("redirect_checker.spawn_workers", mock_spawn_workers):
                        with mock.patch("redirect_checker.sleep", mock_sleep):
                            redirect_checker.main_loop(config=config)

        mock_sleep.assert_called_once_with(config.SLEEP)
        assert mock_spawn_workers.call_count == 0

        redirect_checker.is_run = True

    def test_main_loop_false_status(self):
        pid = 13
        mock_os_getpid = mock.Mock(return_value=pid)

        mock_check_net_status = mock.Mock(return_value=False)

        config = mock.Mock()
        config.WORKER_POOL_SIZE = 2
        config.SLEEP = 1
        config.CHECK_URL = 'CHECK_URL'
        config.HTTP_TIMEOUT = 100

        child = mock.MagicMock()
        active_children = [child, child]
        mock_active_children = mock.Mock(return_value=active_children)

        mock_spawn_workers = mock.Mock()

        mock_sleep = mock.Mock(side_effect=stop_loop)

        with mock.patch("os.getpid", mock_os_getpid):
            with mock.patch("redirect_checker.check_network_status", mock_check_net_status):
                with mock.patch("redirect_checker.active_children", mock_active_children):
                    with mock.patch("redirect_checker.spawn_workers", mock_spawn_workers):
                        with mock.patch("redirect_checker.sleep", mock_sleep):
                            redirect_checker.main_loop(config=config)

        mock_sleep.assert_called_once_with(config.SLEEP)
        assert mock_spawn_workers.call_count == 0
        assert child.terminate.call_count == 2

        redirect_checker.is_run = True

    def test_main(self):
        argv = mock.MagicMock()
        args = mock.MagicMock()

        config = mock.Mock()
        config.LOGGING = mock.Mock()
        config.EXIT_CODE = 13

        with mock.patch("redirect_checker.parse_cmd_args", mock.Mock(return_value=args)):
            with mock.patch("redirect_checker.daemonize", mock.Mock()) as mock_daemonize:
                with mock.patch("redirect_checker.create_pidfile", mock.Mock()) as mock_create_pidfile:
                    with mock.patch("redirect_checker.load_config_from_pyfile", mock.Mock(return_value=config)):
                        with mock.patch("os.path.realpath", mock.Mock()):
                            with mock.patch("os.path.expanduser", mock.Mock()):
                                with mock.patch("redirect_checker.dictConfig", mock.Mock()):
                                    with mock.patch("redirect_checker.main_loop", mock.Mock()):
                                        exit_code = redirect_checker.main(argv)

        mock_daemonize.assert_called()
        mock_create_pidfile.assert_called()
        assert exit_code == config.EXIT_CODE

    def test_main_false_args(self):
        argv = mock.MagicMock()
        args = mock.Mock()
        args.daemon = False
        args.pidfile = False

        config = mock.Mock()
        config.LOGGING = mock.Mock()
        config.EXIT_CODE = 13

        with mock.patch("redirect_checker.parse_cmd_args", mock.Mock(return_value=args)):
            with mock.patch("redirect_checker.daemonize", mock.Mock()) as mock_daemonize:
                with mock.patch("redirect_checker.create_pidfile", mock.Mock()) as mock_create_pidfile:
                    with mock.patch("redirect_checker.load_config_from_pyfile", mock.Mock(return_value=config)):
                        with mock.patch("os.path.realpath", mock.Mock()):
                            with mock.patch("os.path.expanduser", mock.Mock()):
                                with mock.patch("redirect_checker.dictConfig", mock.Mock()):
                                    with mock.patch("redirect_checker.main_loop", mock.Mock()):
                                        exit_code = redirect_checker.main(argv)
        assert mock_daemonize.call_count == 0
        assert mock_create_pidfile.call_count == 0
        assert exit_code == config.EXIT_CODE

