# myCVEs
myCVEs sends you regularly new and updated CVEs for your configured products.
CVEs are fetched from the NIST CVE API on https://services.nvd.nist.gov/rest/json/cves/1.0/ and filtered according to the jobs configured in your jobs directory.

### Requirements:
- Python 3.8 (only tested with 3.9) either on Windows oder Linux.
- A reachable mailserver or an email-Account (e.g. gmail with application password) for sending the emails
- On Linux: cron installed

### Alternative:
- Docker installed (only tested with Linux)

## Installation:

### Linux
    cd /opt    
    git clone https://github.com/mrfoxyfoxy/myCVEs.git	(alternatively you can download the repo manually and paste it to the directory)
    cd /opt/myCVEs
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r src/requirements.txt 
    deactivate
    echo "0 * * * * root /myCVEs/.venv/bin/python3 /myCVEs/src/main.py" >> /etc/crontab && echo "" >> /etc/crontab

### Windows
    open a powershell window

    cd C:\Program Files    
    git clone https://github.com/mrfoxyfoxy/myCVEs.git (alternatively you can download the repo manually and paste it to the directory)
    cd C:\Program Files\myCVEs 
    python3 -m venv .venv
    .venv/Scripts/activate
    pip install -r src/requirements.txt 
    .venv/Scripts/deactivate

    Configuring the Task (alternatively you can configure it manually in the task scheduler):

    $action = New-ScheduledTaskAction -Execute 'C:\Program Files\myCVEs\.venv\Scripts\Python.exe' -Argument 'C:\Program Files\myCVEs\src.main.py'
    $trigger =  New-ScheduledTaskTrigger -Daily -At 0am
    Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "myCVEs" -Description "get new and updated CVEs"
    $Task.Triggers.Repetition.Duration = "P1D"
    $Task.Triggers.Repetition.Interval = "PT1H" 
    $Task = Get-ScheduledTask -TaskName "myCVEs" 
    $Task | Set-ScheduledTask -User "[your_windows_username]"

### Docker
    cd /opt    
    git clone https://github.com/mrfoxyfoxy/myCVEs.git	
    cd /opt/myCVEs
    docker pull python:3.9-slim-bullseye
    docker build . -t mycves:0.1.0
    docker-compose up -d

## Configuration
1. Configure settings.yaml and .secrets.yaml according to the provided comments.
2. Create your jobs according to the sample_job_yaml and remove the sample_job.yaml from the jobs folder.
You should only provide one vendor per job but you can provide as many producty for the vendor as you want. One configuration file may contain multiple jobs.
To get better search results you could look for your products at the CPE dictionary https://nvd.nist.gov/products/cpe.

