import unittest

from dojo_app.tasks import add_task, complete_task, list_tasks, summarize


class TaskTests(unittest.TestCase):
    def test_add_task_normalizes_title(self):
        tasks = []

        task = add_task(tasks, "  write   the lab  ", owner="Barry", priority="high")

        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "write the lab")
        self.assertEqual(task["owner"], "Barry")
        self.assertEqual(task["priority"], "high")
        self.assertFalse(task["done"])

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValueError):
            add_task([], "   ")

    def test_complete_task_is_idempotent(self):
        tasks = []
        task = add_task(tasks, "run quality gate")

        first = complete_task(tasks, task["id"])
        second = complete_task(tasks, task["id"])

        self.assertTrue(first["done"])
        self.assertEqual(first["completed_at"], second["completed_at"])

    def test_list_tasks_filters_owner_and_done_state(self):
        tasks = []
        add_task(tasks, "write tests", owner="Kai")
        done = add_task(tasks, "ship demo", owner="Kai")
        add_task(tasks, "review docs", owner="Nia")
        complete_task(tasks, done["id"])

        found = list_tasks(tasks, owner="Kai", include_done=False)

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["title"], "write tests")

    def test_summarize_counts_status(self):
        tasks = []
        add_task(tasks, "add rule", priority="high")
        done = add_task(tasks, "save note")
        complete_task(tasks, done["id"])

        self.assertEqual(
            summarize(tasks),
            {"total": 2, "open": 1, "done": 1, "high_priority": 1},
        )


if __name__ == "__main__":
    unittest.main()

