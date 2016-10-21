import unittest
from core.flows import BaseFlow
from core.config import BaseGlobalConfig
from core.config import BaseProjectConfig
from core.config import OrgConfig

class TestBaseFlow(unittest.TestCase):
    flow_class = BaseFlow

    def setUp(self):
        self.global_config = BaseGlobalConfig()
        self.project_config = BaseProjectConfig(self.global_config)
        self.org_config = OrgConfig({'foo': 'bar'})

    def test_init(self):
        self._test_init()

    def _test_init(self):
        flow_config = {}
        flow = BaseFlow(self.project_config, flow_config, self.org_config)
        self.assertEquals(hasattr(flow, 'logger'), True)

    def test_call_no_tasks(self):
        self._test_call_no_tasks()

    def _test_call_no_tasks(self):
        pass

    def test_call_one_task(self):
        self._test_call_no_tasks()

    def _test_call_no_tasks(self):
        pass

    def test_call_many_tasks(self):
        self._test_call_many_tasks()

    def _test_call_many_tasks(self):
        pass

    def test_call_task_not_found(self):
        self._test_call_task_not_found()

    def _test_call_task_not_found(self):
        pass
