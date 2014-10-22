import mock
import requests
import unittest
from notification_pusher import create_pidfile, notification_worker, done_with_processed_tasks
import notification_pusher


def stop_main_loop(*args, **kwargs):
    notification_pusher.run_application=False


class NotificationPusherTestCase(unittest.TestCase):
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_notification_worker(self):
        task = mock.Mock()
        task.data.copy = mock.Mock(return_value={"callback_url": "callback_url"})
        task.task_id = 13

        task_queue = mock.Mock()

        response = mock.Mock()
        response.status_code = mock.Mock()

        with mock.patch("requests.post", mock.Mock(return_value=response)):
            notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, "ack"))

    def test_notification_worker_exception(self):
        task = mock.Mock()
        task.data.copy = mock.Mock(return_value={"callback_url": "callback_url"})
        task.task_id = 15

        task_queue = mock.Mock()

        response = requests.RequestException("ERROR")

        with mock.patch("requests.post", mock.Mock(side_effect=response)):
            notification_worker(task, task_queue)

        task_queue.put.assert_called_with((task, "bury"))

    def test_done_with_processed_tasks(self):
        task = mock.Mock()
        task.task_id = mock.Mock()
        task.action_name = mock.Mock()

        qsize = 3

        task_queue = mock.Mock()
        task_queue.get_nowait = mock.Mock(return_value= (task, "action_name"))
        task_queue.qsize = mock.Mock(return_value=qsize)

        done_with_processed_tasks(task_queue)

        self.assertTrue(task.action_name.call_count == qsize)

    def test_done_with_processed_tasks_db_exception(self):
        task = mock.Mock()
        task.task_id = mock.Mock()
        task.action_name = mock.Mock()

        task_queue = mock.Mock()
        task_queue.get_nowait = mock.Mock(return_value=(task, "action_name"))
        task_queue.qsize = mock.Mock(return_value=1)

        import tarantool
        task.action_name = mock.Mock(side_effect=tarantool.DatabaseError())
        logger = mock.Mock()
        with mock.patch("notification_pusher.logger", logger):
            done_with_processed_tasks(task_queue)

        self.assertTrue(logger.exception.called)

    def test_done_with_processed_tasks_queue_empty_exception(self):
        task = mock.Mock()
        task.task_id = mock.Mock()
        task.action_name = mock.Mock()

        task_queue = mock.Mock()
        task_queue.qsize = mock.Mock(return_value=1)

        import gevent.queue as gevent_queue
        task_queue.get_nowait = mock.Mock(side_effect=gevent_queue.Empty)

        logger = mock.Mock()

        with mock.patch("notification_pusher.logger", logger):
            done_with_processed_tasks(task_queue)

        self.assertFalse(logger.exception.called)
        self.assertFalse(task.action_name.called)

    def test_stop_handler(self):
        run_app = notification_pusher.run_application
        exit_code = notification_pusher.exit_code
        signum = 13
        notification_pusher.stop_handler(signum)
        self.assertTrue(notification_pusher.run_application == False)
        self.assertTrue(notification_pusher.exit_code == notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum)

        notification_pusher.run_application = run_app
        notification_pusher.exit_code = exit_code

    def test_main_loop_run_app_no_task(self):
        config = mock.MagicMock()
        config.QUEUE_HOST = 'queue_host'
        config.QUEUE_PORT = 8080
        config.QUEUE_SPACE = 1
        config.QUEUE_TUBE = 'queue_tube'
        config.QUEUE_TAKE_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 1
        config.SLEEP = 1
        config.HTTP_CONNECTION_TIMEOUT = 2

        tube = mock.MagicMock()
        tube.take = mock.Mock(return_value=False)
        queue = mock.MagicMock()
        queue.tube = mock.Mock(return_value=tube)

        processed_task_queue = mock.MagicMock()

        worker_pool = mock.Mock()
        worker_pool.free_count = mock.Mock(return_value=1)

        mock_done_with_processed_tasks = mock.Mock()
        mock_logger = mock.Mock()
        mock_sleep = mock.Mock(side_effect=stop_main_loop)

        with mock.patch("notification_pusher.logger", mock_logger):
            with mock.patch("notification_pusher.tarantool_queue.Queue", mock.Mock(return_value=queue)):
                with mock.patch("notification_pusher.Pool", mock.Mock(return_value=worker_pool)):
                    with mock.patch("notification_pusher.gevent_queue.Queue", mock.Mock(return_value=processed_task_queue)):
                        with mock.patch("notification_pusher.done_with_processed_tasks", mock_done_with_processed_tasks):
                            with mock.patch("notification_pusher.sleep", mock_sleep):
                                with mock.patch("notification_pusher.run_application", True):
                                    notification_pusher.main_loop(config)

        worker_pool.free_count.assert_called_once_with()
        tube.take.assert_called_once_with(config.QUEUE_TAKE_TIMEOUT)
        mock_done_with_processed_tasks.assert_called_once_with(processed_task_queue)
        mock_sleep.assert_called_once_with(config.SLEEP)
        self.assertTrue(mock_logger.debug.call_count == 2)
        self.assertFalse(worker_pool.add.called)

    def test_main_loop_run_app_with_task(self):
        config = mock.MagicMock()
        config.QUEUE_HOST = 'queue_host'
        config.QUEUE_PORT = 8080
        config.QUEUE_SPACE = 1
        config.QUEUE_TUBE = 'queue_tube'
        config.QUEUE_TAKE_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 1
        config.SLEEP = 1
        config.HTTP_CONNECTION_TIMEOUT = 2

        task = mock.MagicMock()
        tube = mock.MagicMock()
        tube.take = mock.Mock(return_value=task)
        queue = mock.MagicMock()
        queue.tube = mock.Mock(return_value=tube)

        processed_task_queue = mock.MagicMock()

        worker_pool = mock.Mock()
        worker_pool.free_count = mock.Mock(return_value=1)

        mock_done_with_processed_tasks = mock.Mock()
        mock_logger = mock.Mock()
        mock_sleep = mock.Mock(side_effect=stop_main_loop)

        with mock.patch("notification_pusher.logger", mock_logger):
            with mock.patch("notification_pusher.tarantool_queue.Queue", mock.Mock(return_value=queue)):
                with mock.patch("notification_pusher.Pool", mock.Mock(return_value=worker_pool)):
                    with mock.patch("notification_pusher.gevent_queue.Queue", mock.Mock(return_value=processed_task_queue)):
                        with mock.patch("notification_pusher.done_with_processed_tasks", mock_done_with_processed_tasks):
                            with mock.patch("notification_pusher.sleep", mock_sleep):
                                with mock.patch("notification_pusher.run_application", True):
                                    notification_pusher.main_loop(config)

        worker_pool.free_count.assert_called_once_with()
        tube.take.assert_called_once_with(config.QUEUE_TAKE_TIMEOUT)
        mock_done_with_processed_tasks.assert_called_once_with(processed_task_queue)
        mock_sleep.assert_called_once_with(config.SLEEP)
        self.assertTrue(mock_logger.debug.call_count == 2)
        self.assertTrue(worker_pool.add.called)

    def test_main_loop_not_run_app(self):
        config = mock.Mock()
        config.QUEUE_HOST = 'queue_host'
        config.QUEUE_PORT = 8080
        config.QUEUE_SPACE = 1
        config.QUEUE_TUBE = 'queue_tube'
        config.QUEUE_TAKE_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 1
        config.SLEEP = 1
        config.HTTP_CONNECTION_TIMEOUT = 2

        tube = mock.MagicMock()
        tube.take = mock.Mock(return_value=False)
        queue = mock.MagicMock()
        queue.tube = mock.Mock(return_value=tube)

        processed_task_queue = mock.MagicMock()

        mock_worker_pool = mock.Mock()
        mock_worker_pool.free_count = mock.Mock(return_value=1)

        mock_done_with_processed_tasks = mock.Mock()
        mock_logger = mock.Mock()
        mock_sleep = mock.Mock(side_effect=stop_main_loop)

        with mock.patch("notification_pusher.logger", mock_logger):
            with mock.patch("notification_pusher.tarantool_queue.Queue", mock.Mock(return_value=queue)):
                with mock.patch("notification_pusher.Pool", mock.Mock(return_value=mock_worker_pool)):
                    with mock.patch("notification_pusher.gevent_queue.Queue", mock.Mock(return_value=processed_task_queue)):
                        with mock.patch("notification_pusher.done_with_processed_tasks", mock_done_with_processed_tasks):
                            with mock.patch("notification_pusher.sleep", mock_sleep):
                                with mock.patch("notification_pusher.run_application", False):
                                    notification_pusher.main_loop(config)

        self.assertFalse(mock_done_with_processed_tasks.called)
        self.assertFalse(mock_sleep.called)

    def test_parse_cmd_args(self):
        arg = mock.Mock()
        args = [arg, arg]
        parser = mock.Mock()
        with mock.patch("notification_pusher.argparse.ArgumentParser", mock.Mock(return_value=parser)):
            notification_pusher.parse_cmd_args(args)

        parser.parse_args.assert_called_once_with(args=args)

    def test_daemonize(self):
        pid = 13
        with mock.patch("notification_pusher.os.fork", mock.Mock(return_value=pid)) as mock_os_fork:
            with mock.patch("notification_pusher.os._exit", mock.Mock()) as mock_os_exit:
                notification_pusher.daemonize()

        mock_os_fork.assert_called_once_with()
        mock_os_exit.assert_called_once_with(0)

    def test_daemonize_pid_zero(self):
        pid = 0
        with mock.patch("notification_pusher.os.fork", mock.Mock(return_value=pid)) as mock_os_fork:
            with mock.patch("notification_pusher.os.setsid", mock.Mock()) as mock_os_setsid:
                notification_pusher.daemonize()

        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count == 2)

    def test_daemonize_pid_zero_not_zero(self):
        pid = 13
        with mock.patch("notification_pusher.os.fork", mock.Mock(side_effect=[0, pid])) as mock_os_fork:
            with mock.patch("notification_pusher.os.setsid", mock.Mock()) as mock_os_setsid:
                with mock.patch("notification_pusher.os._exit", mock.Mock()) as mock_os_exit:
                    notification_pusher.daemonize()

        mock_os_setsid.assert_called_once_with()
        mock_os_exit.assert_called_once_with(0)
        self.assertTrue(mock_os_fork.call_count == 2)

    def test_daemonize_oserror(self):
        with mock.patch("notification_pusher.os.fork", mock.Mock(side_effect=OSError)) as mock_os_fork:
            self.assertRaises(Exception, notification_pusher.daemonize)

        mock_os_fork.assert_called_once_with()

    def test_daemonize_pid_zero_oserror(self):
        with mock.patch("notification_pusher.os.fork", mock.Mock(side_effect=[0, OSError])) as mock_os_fork:
            with mock.patch("notification_pusher.os.setsid", mock.Mock()) as mock_os_setsid:
                self.assertRaises(Exception, notification_pusher.daemonize)

        mock_os_setsid.assert_called_once_with()
        self.assertTrue(mock_os_fork.call_count == 2)

    def test_load_config_from_pyfile(self):
        result = notification_pusher.load_config_from_pyfile('source/tests/test_config.py')
        self.assertEqual(result.CONF_KEY, 1)
        self.assertEqual(result.CONF_KEY_1, 'value')
        self.assertFalse(hasattr(result, 'Conf_Key_2'))
        self.assertEqual(result.CONF_KEY_THREE, {
            'value_key_1': 'value_1',
            'value_key_2': 'value_2'
        })

    def test_install_signal_handlers(self):
        mock_signal = mock.Mock()
        mock_signal.SIGTERM = 13
        mock_signal.SIGINT = 13
        mock_signal.SIGHUP = 13
        mock_signal.SIGQUIT = 13

        with mock.patch('gevent.signal', mock_signal):
            notification_pusher.install_signal_handlers()

        self.assertTrue(mock_signal.call_count == 4)

    def test_main_daemon_pidfile_app_not_run(self):
        argv = mock.MagicMock()
        args = mock.Mock()
        args.daemon = True
        args.pidfile = True

        mock_parse = mock.Mock(return_value=args)
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        mock_main_loop = mock.Mock(side_effect=stop_main_loop)

        with mock.patch("notification_pusher.parse_cmd_args", mock_parse):
            with mock.patch("notification_pusher.daemonize", mock_daemonize):
                with mock.patch("notification_pusher.create_pidfile", mock_create_pidfile):
                    with mock.patch("notification_pusher.load_config_from_pyfile", mock.Mock()):
                        with mock.patch("os.path.realpath", mock.Mock()):
                            with mock.patch("os.path.expanduser", mock.Mock()):
                                with mock.patch("notification_pusher.load_config_from_pyfile", mock.Mock()):
                                    with mock.patch("notification_pusher.patch_all", mock.Mock()):
                                        with mock.patch("notification_pusher.dictConfig", mock.Mock()):
                                            with mock.patch("notification_pusher.install_signal_handlers", mock.Mock()):
                                                with mock.patch("notification_pusher.run_application", False):
                                                    with mock.patch("notification_pusher.main_loop", mock_main_loop):
                                                        code = notification_pusher.main(argv)

        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called_once_with(args.pidfile)
        self.assertTrue(code == notification_pusher.exit_code)

    def test_main_daemonize_no_pidfile_app_not_run(self):
        argv = mock.MagicMock()
        args = mock.Mock()
        args.daemon = False
        args.pidfile = False

        mock_parse = mock.Mock(return_value=args)
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        mock_main_loop = mock.Mock(side_effect=stop_main_loop)

        with mock.patch("notification_pusher.parse_cmd_args", mock_parse):
            with mock.patch("notification_pusher.daemonize", mock_daemonize):
                with mock.patch("notification_pusher.create_pidfile", mock_create_pidfile):
                    with mock.patch("notification_pusher.load_config_from_pyfile", mock.Mock()):
                        with mock.patch("os.path.realpath", mock.Mock()):
                            with mock.patch("os.path.expanduser", mock.Mock()):
                                with mock.patch("notification_pusher.load_config_from_pyfile", mock.Mock()):
                                    with mock.patch("notification_pusher.patch_all", mock.Mock()):
                                        with mock.patch("notification_pusher.dictConfig", mock.Mock()):
                                            with mock.patch("notification_pusher.install_signal_handlers", mock.Mock()):
                                                with mock.patch("notification_pusher.run_application", False):
                                                    with mock.patch("notification_pusher.main_loop", mock_main_loop):
                                                        code = notification_pusher.main(argv)

        self.assertFalse(mock_daemonize.called)
        self.assertFalse(mock_create_pidfile.called)
        self.assertTrue(code == notification_pusher.exit_code)

    def test_main_app_run(self):
        argv = mock.MagicMock()
        args = mock.Mock()
        args.daemon = True
        args.pidfile = True

        config = mock.MagicMock()

        mock_parse = mock.Mock(return_value=args)
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        mock_main_loop = mock.Mock(side_effect=stop_main_loop)
        mock_load = mock.Mock(return_value=config)

        with mock.patch("notification_pusher.parse_cmd_args", mock_parse):
            with mock.patch("notification_pusher.daemonize", mock_daemonize):
                with mock.patch("notification_pusher.create_pidfile", mock_create_pidfile):
                    with mock.patch("notification_pusher.load_config_from_pyfile", mock_load):
                        with mock.patch("os.path.realpath", mock.Mock()):
                            with mock.patch("os.path.expanduser", mock.Mock()):
                                with mock.patch("notification_pusher.load_config_from_pyfile", mock.Mock()):
                                    with mock.patch("notification_pusher.patch_all", mock.Mock()):
                                        with mock.patch("notification_pusher.dictConfig", mock.Mock()):
                                            with mock.patch("notification_pusher.install_signal_handlers", mock.Mock()):
                                                with mock.patch("notification_pusher.run_application", True):
                                                    with mock.patch("notification_pusher.main_loop", mock_main_loop):
                                                        code = notification_pusher.main(argv)
        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called_once_with(args.pidfile)
        self.assertTrue(mock_main_loop.called)
        self.assertTrue(code == notification_pusher.exit_code)

    def test_main_app_run_exception(self):
        argv = mock.MagicMock()
        args = mock.Mock()
        args.daemon = True
        args.pidfile = True

        config = mock.MagicMock()
        config.LOGGING - mock.Mock()
        config.SLEEP_ON_FAIL = mock.Mock()

        mock_parse = mock.Mock(return_value=args)
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        mock_main_loop = mock.Mock(side_effect=Exception)
        mock_load = mock.Mock(return_value=config)
        mock_sleep = mock.Mock(side_effect=stop_main_loop)

        with mock.patch("notification_pusher.parse_cmd_args", mock_parse):
            with mock.patch("notification_pusher.daemonize", mock_daemonize):
                with mock.patch("notification_pusher.create_pidfile", mock_create_pidfile):
                    with mock.patch("notification_pusher.load_config_from_pyfile", mock_load):
                        with mock.patch("os.path.realpath", mock.Mock()):
                            with mock.patch("os.path.expanduser", mock.Mock()):
                                with mock.patch("notification_pusher.load_config_from_pyfile", mock.Mock()):
                                    with mock.patch("notification_pusher.patch_all", mock.Mock()):
                                        with mock.patch("notification_pusher.dictConfig", mock.Mock()):
                                            with mock.patch("notification_pusher.install_signal_handlers", mock.Mock()):
                                                with mock.patch("notification_pusher.run_application", True):
                                                    with mock.patch("notification_pusher.main_loop", mock_main_loop):
                                                        with mock.patch("notification_pusher.sleep", mock_sleep):
                                                            code = notification_pusher.main(argv)
        mock_daemonize.assert_called_once_with()
        mock_create_pidfile.assert_called_once_with(args.pidfile)
        self.assertTrue(mock_main_loop.called)
        self.assertTrue(mock_sleep.called)
        self.assertTrue(code == notification_pusher.exit_code)