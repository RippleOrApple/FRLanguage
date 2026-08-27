import unittest

from frlang.future import Future, FutureState


class FutureTest(unittest.TestCase):
    def test_future_starts_pending(self) -> None:
        future = Future()

        self.assertIs(future.state, FutureState.PENDING)

    def test_resolve_completes_future(self) -> None:
        future = Future()

        future.resolve(42)

        self.assertIs(future.state, FutureState.RESOLVED)
        self.assertEqual(future.value, 42)

    def test_reject_fails_future(self) -> None:
        future = Future()
        error = Exception("boom")

        future.reject(error)

        self.assertIs(future.state, FutureState.REJECTED)
        self.assertIs(future.error, error)


if __name__ == "__main__":
    unittest.main()
