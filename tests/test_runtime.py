import unittest

from frlang.runtime import Runtime


class RuntimeTest(unittest.TestCase):
    def test_runs_scheduled_tasks_in_fifo_order(self) -> None:
        runtime = Runtime()
        events: list[str] = []

        runtime.schedule(lambda: events.append("first"))
        runtime.schedule(lambda: events.append("second"))
        runtime.run()

        self.assertEqual(events, ["first", "second"])


if __name__ == "__main__":
    unittest.main()
