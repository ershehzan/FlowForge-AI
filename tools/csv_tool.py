import pandas as pd

def read_jobs_csv(file_path):
    df = pd.read_csv(file_path)
    jobs = df.to_dict(orient='records')
    return jobs
