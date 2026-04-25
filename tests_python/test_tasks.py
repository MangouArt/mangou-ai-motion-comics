from __future__ import annotations

import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path

from mangou_skill.tasks import append_task_event, get_task_by_id, list_latest_tasks


class TaskLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="mangou-tasks-test-")).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def test_crud_lifecycle_for_tasks(self) -> None:
        append_task_event(self.temp_dir, {"id": "task-1", "type": "image", "status": "pending", "input": {"prompt": "A cat"}})
        append_task_event(self.temp_dir, {"id": "task-1", "status": "processing", "worker": "worker-1"})
        append_task_event(self.temp_dir, {"id": "task-1", "status": "success", "output": "cat.png"})
        append_task_event(self.temp_dir, {"id": "task-2", "type": "video", "status": "pending"})

        tasks = list_latest_tasks(self.temp_dir)
        self.assertEqual(len(tasks), 2)
        task_1 = next(task for task in tasks if task["id"] == "task-1")
        self.assertEqual(task_1["status"], "success")
        self.assertEqual(task_1["output"], "cat.png")
        self.assertEqual(get_task_by_id(self.temp_dir, "task-1")["status"], "success")

    def test_handles_concurrent_writes_with_file_lock(self) -> None:
        threads = [
            threading.Thread(target=append_task_event, args=(self.temp_dir, {"id": f"task-{i}", "status": "pending"}))
            for i in range(10)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(list_latest_tasks(self.temp_dir)), 10)

    def test_cleans_stale_lock_files_before_appending(self) -> None:
        lock_path = self.temp_dir / "tasks.jsonl.lock"
        lock_path.write_text("stale", encoding="utf-8")
        stale_time = time.time() - 20
        os_times = (stale_time, stale_time)
        import os
        os.utime(lock_path, os_times)

        snapshot = append_task_event(self.temp_dir, {"id": "task-after-stale-lock", "status": "processing"})
        self.assertEqual(snapshot["id"], "task-after-stale-lock")
        self.assertEqual(get_task_by_id(self.temp_dir, "task-after-stale-lock")["status"], "processing")
