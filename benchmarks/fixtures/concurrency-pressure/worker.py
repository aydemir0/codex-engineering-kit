import asyncio


async def run_job(job):
    await job.execute()


async def process_jobs(jobs):
    await asyncio.gather(*(run_job(job) for job in jobs))
