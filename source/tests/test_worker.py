import mock
import unittest
from lib import worker


class WorkerTestCase(unittest.TestCase):
    def test_get_redirect_history_from_task_type_error(self):
        task = mock.Mock()
        task.data = dict(url="url", recheck=False, url_id="url_id")
        task.task_id = 13

        history = [["ERROR"], [], []]
        mock_get_redirect_history = mock.Mock(return_value=history)

        with mock.patch("lib.worker.get_redirect_history", mock_get_redirect_history):
            is_input, data = worker.get_redirect_history_from_task(task=task, timeout=1)

        assert is_input == True
        assert data == task.data

    def test_get_redirect_history_from_task_no_error_no_suspicious(self):
        task = mock.Mock()
        task.data = dict(url="url", recheck=False, url_id="url_id")
        task.task_id = 13

        history = [["type"], ["urls"], ["counters"]]
        mock_get_redirect_history = mock.Mock(return_value=history)

        with mock.patch("lib.worker.get_redirect_history", mock_get_redirect_history):
            is_input, data = worker.get_redirect_history_from_task(task=task, timeout=1)

        assert is_input == False
        assert data["url_id"] == task.data["url_id"]
        assert data["result"] == history
        assert data["check_type"] == "normal"

    def test_get_redirect_history_from_task_no_error_with_suspicious(self):
        task = mock.Mock()
        task.data = dict(url="url", recheck=False, url_id="url_id", suspicious="suspicious")
        task.task_id = 13

        history = [["type"], ["urls"], ["counters"]]
        mock_get_redirect_history = mock.Mock(return_value=history)

        with mock.patch("lib.worker.get_redirect_history", mock_get_redirect_history):
            is_input, data = worker.get_redirect_history_from_task(task=task, timeout=1)

        assert is_input == False
        assert data["url_id"] == task.data["url_id"]
        assert data["result"] == history
        assert data["check_type"] == "normal"
        assert data["suspicious"] == task.data["suspicious"]

    def test_worker_parent_proc_not_exist(self):
        config = mock.MagicMock()
        parent_pid = 13

        input_tube = mock.MagicMock()
        output_tube = mock.MagicMock()
        mock_get_tube = mock.Mock(side_effect=[input_tube, output_tube])

        with mock.patch("lib.worker.get_tube", mock_get_tube):
            with mock.patch("os.path.exists", mock.Mock(return_value=False)):
                worker.worker(config, parent_pid)

        assert input_tube.take.call_count == 0

    def test_worker_parent_proc_exist_not_task(self):
        config = mock.Mock()
        parent_pid = 13

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=None)
        output_tube = mock.MagicMock()
        mock_get_tube = mock.Mock(side_effect=[input_tube, output_tube])

        mock_get_redirect_history_from_task = mock.Mock()

        with mock.patch("lib.worker.get_tube", mock_get_tube):
            with mock.patch("os.path.exists", mock.Mock(side_effect=[True, False])):
                with mock.patch("lib.worker.get_redirect_history_from_task", mock_get_redirect_history_from_task):
                    worker.worker(config, parent_pid)

        assert mock_get_redirect_history_from_task.call_count == 0
        assert input_tube.take.call_count == 1

    def test_worker_parent_proc_exist_task_not_result(self):
        config = mock.Mock()
        parent_pid = 13

        task = mock.MagicMock()
        task.ack = mock.Mock()

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)
        output_tube = mock.MagicMock()
        mock_get_tube = mock.Mock(side_effect=[input_tube, output_tube])

        mock_get_redirect_history_from_task = mock.Mock(return_value=False)

        with mock.patch("lib.worker.get_tube", mock_get_tube):
            with mock.patch("os.path.exists", mock.Mock(side_effect=[True, False])):
                with mock.patch("lib.worker.get_redirect_history_from_task", mock_get_redirect_history_from_task):
                    worker.worker(config, parent_pid)

        assert input_tube.take.call_count == 1
        assert mock_get_redirect_history_from_task.call_count == 1
        assert task.ack.call_count == 1

    def test_worker_parent_proc_exist_task_not_result_exception(self):
        config = mock.Mock()
        parent_pid = 13

        from tarantool import DatabaseError
        task = mock.MagicMock()
        task.ack = mock.Mock(side_effect=DatabaseError)

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)
        output_tube = mock.MagicMock()
        mock_get_tube = mock.Mock(side_effect=[input_tube, output_tube])

        mock_get_redirect_history_from_task = mock.Mock(return_value=False)
        mock_logger = mock.Mock()

        with mock.patch("lib.worker.get_tube", mock_get_tube):
            with mock.patch("os.path.exists", mock.Mock(side_effect=[True, False])):
                with mock.patch("lib.worker.get_redirect_history_from_task", mock_get_redirect_history_from_task):
                    with mock.patch("lib.worker.logger", mock_logger):
                        worker.worker(config, parent_pid)

        assert input_tube.take.call_count == 1
        assert mock_get_redirect_history_from_task.call_count == 1
        assert task.ack.call_count == 1
        assert mock_logger.exception.call_count == 1

    def test_worker_parent_proc_exist_task_result_is_input(self):
        config = mock.Mock()
        parent_pid = 13

        from tarantool import DatabaseError
        task = mock.MagicMock()
        task.ack = mock.Mock(side_effect=DatabaseError)

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)
        output_tube = mock.MagicMock()
        mock_get_tube = mock.Mock(side_effect=[input_tube, output_tube])

        is_input = True
        data = mock.Mock()
        mock_get_redirect_history_from_task = mock.Mock(return_value=[is_input, data])
        mock_logger = mock.Mock()

        with mock.patch("lib.worker.get_tube", mock_get_tube):
            with mock.patch("os.path.exists", mock.Mock(side_effect=[True, False])):
                with mock.patch("lib.worker.get_redirect_history_from_task", mock_get_redirect_history_from_task):
                    with mock.patch("lib.worker.logger", mock_logger):
                        worker.worker(config, parent_pid)

        assert input_tube.take.call_count == 1
        assert mock_get_redirect_history_from_task.call_count == 1
        assert input_tube.put.call_count == 1
        assert task.ack.call_count == 1
        assert mock_logger.exception.call_count == 1

    def test_worker_parent_proc_exist_task_result_no_input(self):
        config = mock.Mock()
        parent_pid = 13

        from tarantool import DatabaseError
        task = mock.MagicMock()
        task.ack = mock.Mock(side_effect=DatabaseError)

        input_tube = mock.MagicMock()
        input_tube.take = mock.Mock(return_value=task)
        output_tube = mock.MagicMock()
        mock_get_tube = mock.Mock(side_effect=[input_tube, output_tube])

        is_input = False
        data = mock.Mock()
        mock_get_redirect_history_from_task = mock.Mock(return_value=[is_input, data])
        mock_logger = mock.Mock()

        with mock.patch("lib.worker.get_tube", mock_get_tube):
            with mock.patch("os.path.exists", mock.Mock(side_effect=[True, False])):
                with mock.patch("lib.worker.get_redirect_history_from_task", mock_get_redirect_history_from_task):
                    with mock.patch("lib.worker.logger", mock_logger):
                        worker.worker(config, parent_pid)

        assert input_tube.take.call_count == 1
        assert mock_get_redirect_history_from_task.call_count == 1
        assert output_tube.put.call_count == 1
        assert task.ack.call_count == 1
        assert mock_logger.exception.call_count == 1
