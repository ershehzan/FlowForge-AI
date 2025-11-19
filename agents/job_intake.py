def load_jobs_from_list(records):
    jobs = []
    for r in records:
        jobs.append({
            'job_id': r['job_id'],
            'duration': int(r['processing_time']),
            'due': int(r['due_date'])
        })
    return jobs
