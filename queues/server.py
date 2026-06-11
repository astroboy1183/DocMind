import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rq import Queue
from rq.job import Job

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(host="localhost", port=6379)
q = Queue(connection=r)


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def root():
    return {"status": "server up and running"}


@app.post("/query")
def enqueue_query(request: QueryRequest):
    job = q.enqueue("queues.worker.process_query", request.query)
    return {"job_id": job.id}


@app.get("/result/{job_id}")
def get_result(job_id: str):
    job = Job.fetch(job_id, connection=r)

    if job.is_finished:
        return {"status": "completed", "result": job.result}
    elif job.is_failed:
        return {"status": "failed", "result": None}
    else:
        return {"status": "pending", "result": None}
