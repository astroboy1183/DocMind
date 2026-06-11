"""CLI client for the RAG queue — enqueues a query and polls for the result.

Use this when you want to test the queue from the terminal without the React frontend.
Requires the RQ worker and Valkey/Redis to be running (start docker compose first).
"""

import time
import redis
from rq import Queue
from rq.job import Job

r = redis.Redis(host="localhost", port=6379)
q = Queue(connection=r)


def main():
    print("RAG Queue CLI client  (type 'quit' to exit)\n")

    while True:
        query = input("Ask: ").strip()
        if not query or query.lower() in ("quit", "exit"):
            break

        job = q.enqueue("queues.worker.process_query", query)
        print(f"  Enqueued [{job.id}] — waiting for worker...")

        while True:
            job = Job.fetch(job.id, connection=r)
            if job.is_finished:
                print(f"\nAnswer: {job.result}\n")
                break
            if job.is_failed:
                print("\nJob failed.\n")
                break
            time.sleep(0.5)


if __name__ == "__main__":
    main()
