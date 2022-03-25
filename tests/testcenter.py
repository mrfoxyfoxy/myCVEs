from typing import List, Dict, Union

def traverse_json(data: Union[dict, list], index: str):    
    if isinstance(data, dict):
        return data.get(index)
    elif isinstance(data, list):
        return [traverse_json(da, index) for da in data]
    else:
        return None

def recursive_get(data: dict, *indices):    
    results = data
    for index in indices:
        results = traverse_json(results, index)  
        if results is None: 
            return results
        
    if isinstance(results, list) and isinstance(results[0], list):
        return [r for res in results for r in res] 
    else:
        return results
'''
def test():
    with urlopen(url) as response:
        data = json.load(response)
        dates = data["result"]["CVE_Items"]
        res = [CVEReport(d) for d in dates]
        
        for r in res:
            if "fortinet" in r.cve.assigner:
                print(r.cve.description)
        
        filter_res = [r for r in res if filter_cve_reports(r, devices)]
        """
        for f in filter_res:
            print(f.cve)
            print(f.cpes)
            print(f.cve_scores)
        """

'''
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


path = Path("jobs")


@dataclass
class Job:
    """Job from a configuration file that should be run against the database"""
    starttime: int
    interval: int
    updates: bool
    vendor: str
    products: list
    

def get_hour():
    """round time to current hour"""
    return datetime.now().hour if datetime.now().minute < 30 else datetime.now().hour +1

def get_jobs(path: Path):
    """read jobs from configuration folger"""
    jobs: list = []
    for file in path.iterdir():       
        with file.open("r") as config:            
            job = yaml.safe_load(config)            
            jobs.extend(
                Job(
                    starttime = job["starttime"],
                    interval = job["interval"],
                    updates = job["updates"],
                    **device
                ) for device in job["devices"])    
    return jobs

def get_job_status(job: dict):
    """determine if a job has to be run now"""    
    return not bool((get_hour() -job["starttime"]) % job["interval"])

def fitler_job(jobs: list):    
    """filter jobs that have to be run now"""
    return list(filter(get_job_status, jobs))
    
def get_current_jobs(path):
    """get jobs for new published cves and for updates cves"""
    jobs = get_jobs(path)
    pub_jobs = fitler_job(jobs)
    mod_jobs = filter(lambda job: job["updates"]==True, pub_jobs)
    return pub_jobs, mod_jobs


#get_jobs(path)


fmt = "%Y-%m-%d %H:%M:%S"


def get_last_run_time_stamp():
    try:
        with open("last_run.txt", mode="r") as file:
            print(datetime.strptime(file.read(), fmt))
            return datetime.strptime(file.read(), fmt)
    except:
        print(datetime.now().strftime(fmt))
        print(type(datetime.now().strftime(fmt)))
        return datetime.now().strftime(fmt)

def save_last_run_time_stamp():
       # update the script execution time and save it to the file
    with open("last_run.txt", mode="w") as file:
        current_timestamp = datetime.now().strftime(fmt)
        print(current_timestamp)
        print(type(current_timestamp))
        file.write(current_timestamp)
        
#get_last_run_time_stamp()
#save_last_run_time_stamp()

from itertools import groupby
a = (
    (1,10,100),
    (1,12,102),
    (2,20,200),
    (2,22,202),
    (2,21,101),
    (2,21,201),
    (3,30,300),
    (3,31,301),
    (3,32,202)
)
z = a# sorted(a, key=lambda x: (x[0], x[1]))
x = groupby(z, lambda y: (y[0], y[1]))

 
#for g_key, sub_iter in x:
#    print(g_key, list(sub_iter))
from datetime import timedelta
from operator import attrgetter
@dataclass
class X:
    last_updated: datetime
    interval: int
    

datetime(2022, 3, 1, 12, 5, 1)
r = [X(datetime(2022, 3, 1, 12, 5, 1),3),
     X(datetime(2022, 3, 1, 12, 5, 1),2),
     X(datetime(2022, 3, 1, 12, 5, 5),3),
     X(datetime(2022, 3, 1, 12, 5, 1),3)]

def round_time(date: datetime) -> datetime:
    """round time to munutes"""
    return date - timedelta(seconds=date.second,microseconds=date.microsecond)

def create_job_groups(jobs: list) -> list:
    """group jobs by last update time and interval to make only one api request per group"""    
    sorted_jobs = sorted(jobs, key=lambda job: (round_time(job.last_updated), job.interval))    
    grouped_jobs = groupby(sorted_jobs, lambda job: (round_time(job.last_updated), job.interval))
    job_list = [list(jobs[1]) for jobs in grouped_jobs]
    for j in job_list:
        print(j)
    return job_list
    
        
#create_job_groups(r)
a = [[1,2],[3,4],[5,5, 6]]
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
"""
env = Environment(
        loader=FileSystemLoader('templates'))#,
        #autoescape=select_autoescape(['html'])
    #)
template = env.get_template("table.html")
with open("tset.json", "r") as f:
    data = json.load(f)
x = template.render(results=data)
with open("test.html", "w") as f:
    f.write(x)
print(x)
"""
import aiofiles
import asyncio
from pathlib import Path

path = Path("testfile.txt")
conf_path = path.joinpath("jobs")
def read_files():
    b = []
    for file in Path.cwd().joinpath("jobs").iterdir():
        with file.open("r") as f:
            a = f.read()
            b.append(a)

async def async_read_file(path: Path, encoding:str ="utf-8"):
    async with aiofiles.open(path, "r", encoding=encoding) as file:        
        return await file.read()
           
async def async_read_files(files: list[Path]):
    read_operations = [asyncio.create_task(async_read_file(file)) for file in files]
    return await asyncio.gather(*read_operations)
        


async def bla():
    data = await async_read_files(Path.cwd().joinpath("jobs").iterdir())
        
from timeit import timeit

#print(timeit("asyncio.run(bla())", number=1000, globals=globals()))
#print(timeit("read_files()", number=1000, globals=globals()))
from dataclasses import dataclass
from random import randint
from contextlib import AsyncExitStack

async def do_stuff(x):    
    await asyncio.sleep(x)
    print(x)
    return x

async def do_more_stuff(y: set): 
    results = [x.result() for x in y]
    await asyncio.sleep(sum(results)/len(results))
    new_tasks = [print(f'more: {z*z}')  for z in results]
    
    
async def wait():
    numbers = (randint(1,5) for x in range(10))
    api_tasks =[asyncio.create_task(do_stuff(n)) for n in numbers]
    email_tasks = []
    while api_tasks:
        done, pending = await asyncio.wait(api_tasks, return_when=asyncio.FIRST_COMPLETED)
        print(f'done: {[d.result() for d in done]}')
        email_tasks.append(asyncio.create_task(do_more_stuff(done)))
        api_tasks = pending
    print("exit loop")
    await asyncio.gather(*email_tasks)
    #for task in email_tasks:
        #await task

#asyncio.run(wait())
        
async def job_pipeline():    
    api_tasks =[asyncio.create_task(do_stuff(n)) for n in numbers]
    email_tasks = []
    while api_tasks:
        done, pending = await asyncio.wait(api_tasks, return_when=asyncio.FIRST_COMPLETED)        
        email_tasks.append(asyncio.create_task(do_more_stuff(done)))
        api_tasks = pending    
    await asyncio.gather(*email_tasks)
    #for task in email_tasks:

from contextlib import AsyncExitStack
async def job_pipeline():    
    jobs = get_current_jobs(settings)
    if jobs:
        job_groups = create_job_groups(jobs)
    async with AsyncExitStack() as stack:
        client = await stack,enter_async_context(httpx.AsyncClient())
        client = await stack.enter_async_context()
        
params_pub = {
    "pubStartDate": "2022-03-01T00:00:00:000 UTC%2B01:00",
    "pubEndDate": "2022-03-03T00:00:00:000 UTC%2B01:00",
    "resultsPerPage": "50",
    "keyword": "fortinet"
}

params_mod = {
    "modStartDate": "2022-03-01T00:00:00:000 UTC+01:00",
    "modEndDate": "2022-03-03T00:00:00:000 UTC+01:00",
    "resultsPerPage": "50",
    "keyword": "fortinet"
}

url = "https://services.nvd.nist.gov/rest/json/cves/1.0/"

import httpx

def build_url(params: dict) -> str:    
    """build url with query parametes
    this function is needed because httpx seems to have a bug, giving colons a wrong decoding when used in a param"""
    params_ = f'?{"&".join([f"{key}={value}" for key, value in params.items()])}'
    print(params_)
    return params_

async def blubb():
    async with httpx.AsyncClient(base_url=url) as client:        
        reps = await client.get("/",params=params_mod)
        print(reps.url)
        print(reps.status_code)
        #print(reps.json())

#asyncio.run(blubb())
import aiosmtplib

async def xxx():
    server = aiosmtplib.SMTP("hallo", 25)
    
def bbb(*args, dieter="hering", **kwargs):
    print(args)
    print(kwargs)

from contextlib import contextmanager

@contextmanager
def aaa(func):
    try:
        x = func()
        yield func()
    finally:
        pass
def ccc():
    return 5

#with aaa(ccc) as x:
    #print(x)
    
class DieterError(Exception): pass

async def div(x):    
    if x == 0:
        raise DieterError("Heringe!")
    return (5/x)
    
async def abc():
    x = [1,2,3,0,5]
    try:
        res = await asyncio.gather(*(div(_) for _ in x), return_exceptions=True)
    except Exception as e:
        print("bla")
    #for y in x:
        #print(5/y)
    print(res)
    for r in res:
        #print(type(r))
        if isinstance(r, Exception):
            print(r)
            #print(r.with_traceback(None))
            


from contextvars import ContextVar
from typing import Optional
@dataclass
class Dieter:
    name: str = "Dieter"

@dataclass
class Hering:
    werfer: ContextVar[Dieter]
    
async def hundefutter():
    dieter: ContextVar[Optional[Dieter]] = ContextVar("dieter", default=None)
    dieter.set(Dieter())
    salzi = Hering(dieter)
    print(salzi.werfer.get())    
    for x in ("Gusti", "markus", "benjamin"):
        dieter.set(Dieter(x))
        print(salzi.werfer.get())    
        
#asyncio.run(hundefutter())

def handle_exception(loop, context):
    # context["message"] will always be there; but context["exception"] may not
    msg = context.get("exception", context["message"])    
    #print(dir(context))
    print(f"Caught exception: {msg}")    

async def kram():        
    try:
        y, z = 1, 0
        print(y/z)
    except Exception as e:
        print(f'retrieved {e}')
    #await asyncio.sleep(3)
    x = 1/0
    
    print("hallo")
    """
    loop = asyncio.get_running_loop()
    tasks = [t for t in asyncio.all_tasks() if t is not
            asyncio.current_task()]

    await asyncio.gather(*tasks, return_exceptions=True)
    [task.cancel() for task in tasks]
    loop.stop()
    """
async def blabber():
    print(5)
    asyncio.create_task(kram())
    print(6)
    
    
def main():    
    loop = asyncio.get_event_loop()    
    #loop.set_exception_handler(handle_exception)    
    loop.run_until_complete(blabber())
    
#main()

async def do(x):
    return 1/x

async def one():
    #a = asyncio.create_task(do(0))
    a = asyncio.gather(do(0), return_exceptions=True)
    print("ok")
    b = await a
    print("ok")
    print(b)
    print("ok")
    
@dataclass
class Job:
    """Job from a configuration file that should be run against the cve database"""
    starttime: int
    interval: int
    updates: bool
    send_to: str
    vendor: str
    products: list
    file: str
    last_run: datetime
    
def get_jobs():
    """read jobs from the configuration folder"""
    all_jobs: list = []
    for file in Path.cwd().joinpath("jobs").iterdir():       
        with file.open("r") as config:            
            jobs = yaml.safe_load(config)               
            all_jobs.extend(
                Job(
                    starttime = jobs["starttime"],
                    interval = jobs["interval"],
                    updates = jobs["updates"],
                    send_to = jobs["send_to"],
                    file=file.parts[-1],
                    last_run=datetime.now(),
                    **job
                ) for job in jobs["jobs"])    
    return all_jobs


def get_jobs():
    """read jobs from the configuration folder"""    
    for file in Path.cwd().joinpath("jobs").iterdir():       
        with file.open("r") as config:            
            jobs = yaml.safe_load(config)               
            for job in jobs["jobs"]:
                yield Job(
                    starttime = jobs["starttime"],
                    interval = jobs["interval"],
                    updates = jobs["updates"],
                    send_to = jobs["send_to"],
                    file=file.parts[-1],
                    last_run=datetime.now(),
                    **job
                )  
    
def get_job_status(job: Job) -> bool:
    """determine if a job has to be run now"""
    current_hour = datetime.now().hour if datetime.now().minute < 30 else datetime.now().hour +1      
    return not bool((current_hour -job.starttime) % job.interval)

def filter_jobs(jobs: list):  
    """filter for all jobs that have to be run now"""
    return filter(get_job_status, jobs)    

def get_current_jobs() -> list[Job]:
    """get jobs for new published cves and for updates cves"""
    jobs = get_jobs()
    current_jobs = filter_jobs(jobs)     
    return list(current_jobs)

def create_job_groups() -> list:
    """group jobs by last update time and interval to make only one api request per group"""    
    current_jobs = get_current_jobs()
    sorted_jobs = sorted(current_jobs, key=lambda job: (round_time(job.last_run), job.interval))    
    grouped_jobs = groupby(sorted_jobs, lambda job: (round_time(job.last_run), job.interval))
    return (jobs[1] for jobs in grouped_jobs)



async def gen():
    for x in range(10):
        print(x)
        await asyncio.sleep((x*0.5))
        yield x

async def main():
    async for x in gen():
        print(f'got {x}')

async def m():
    await asyncio.gather(main(), main())

from abc import ABC
from dataclasses import InitVar, field, asdict

@dataclass
class File(ABC):
    
    _path: InitVar[str]
    path: Path = field(init=False)
    
    def __post_init__(self, _path):
        self.path = Path(_path)
   
    def load(self):
        raise NotImplementedError
    
    def dump(self, data):
        raise NotImplementedError
    
    
@dataclass
class YamlFile(File):
    
    _path: InitVar[str]
    path: Path = field(init=False)
    
    def __post_init__(self, _path):
        self.path = Path(_path)
        import yaml
       
    def load(self):
        with self.path.open("r") as f:
            return yaml.safe_load(f)
    
    def dump(self, data):
        with self.path.open("w") as f:
            yaml.safe_dump(data)
       


async def fetch(host, port):
    r, w = await asyncio.open_connection(host, port, ssl=sslctx)
    req = "GET / HTTP/1.1\r\n"
    req += f"Host: {host}\r\n"
    req += "Connection: close\r\n"
    req += "\r\n"

    # send request
    w.write(req.encode())

    # recv response
    resp = ""
    while True:
        line = await r.readline()
        if not line:
            break
        line = line.decode("utf-8")
        resp += line

    # close writer
    w.close()
    await w.wait_closed()
    return resp

a= {1:2, 3:4}
c= {1:2, 3:5}
b= {1:2, 3:4}

print(sorted([a,c,b], key=lambda x: (tuple(x.keys()), tuple(x.values()))))