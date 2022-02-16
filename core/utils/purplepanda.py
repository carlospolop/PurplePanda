from xmlrpc.client import Boolean
import shodan
import os
import ipaddress
import logging
import time
import dns.resolver
import ipaddress
import yaml
from shutil import which
from py2neo.integration import Table

from core.db.customogm import graph

from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    SpinnerColumn,
)

from core.models.models import PublicIP, PublicPort
from concurrent.futures import ThreadPoolExecutor

PROGRESS = Progress(
    TextColumn("[bold blue]{task.fields[task_name]}", justify="right"),
    TextColumn("[yellow]{task.fields[subtask_name]}"),
    BarColumn(bar_width=40),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    TextColumn("[yellow]{task.fields[ttotal]}"),
    "•",
    TimeElapsedColumn(),
    SpinnerColumn()
)


POOL = ThreadPoolExecutor(max_workers=15)

VERBOSE = False
def set_verbose(verbose: bool):
    global VERBOSE
    VERBOSE = verbose

class PurplePanda():
    logger = logging.getLogger(__name__)

    def __init__(self):
        global progress
        self.progress = PROGRESS
    
    def discover(self) -> None:
        self._disc()
    
    def _disc(self) -> None:
        raise Exception(f"_disc not implemented in {self.__class__}")
    
    
    def _disc_loop(self, loop_list, func, subtask_name, **kwargs) -> None:
        """Given a list to iterate though and the function to call with each item of the list, go through it createing a prograss bar"""

        start = time.time()
        task_id = self.progress.add_task(self.task_name, task_name=self.task_name, subtask_name=subtask_name, ttotal=len(loop_list), total=len(loop_list), start=True)
        for item in loop_list:
            func(item, **kwargs)
            self.progress.update(task_id, advance=1)
        
        if not VERBOSE:
            self.progress.update(task_id, visible=False)
        
        end = time.time()
        self.progress.log(f"{subtask_name} took {int(end-start)}s")


    def get_open_ports(self, ip_obj: PublicIP) -> None:
        '''Find open ports of public IP addresses using shodan'''
        
        ip_address = ip_obj.ip
        if ipaddress.ip_address(ip_address).is_private or not os.getenv("SHODAN_KEY"):
            return
        
        shodan_api = shodan.Shodan(os.getenv("SHODAN_KEY"))
        try:
            host_info = shodan_api.host(ip_address)
        
        except shodan.APIError as e:
            if "No information available" in str(e):
                pass
            else:
                self.logger.error(f"Error with shodan accessing host {ip_address}: {e}")
            return

        shodan_data = host_info.get("data", [])
        for entry in shodan_data:
            port = entry["port"]
            transport = entry["transport"]
            port_obj = PublicPort(port=port).save()
            ip_obj.ports.update(port_obj, transport=transport)
        
        ip_obj.save()
        time.sleep(0.5)
    
    def get_domain_ips(self, domain):
        """Given a domain find the IPv4s and IPv6s"""
        
        ips = set()
        
        try:
            answers = dns.resolver.resolve(domain, 'A')
            for ip in answers:
                ips.add(str(ip))
        except:
            pass
        
        try:
            answers = dns.resolver.resolve(domain, 'AAAA')
            for ip in answers:
                ips.add(str(ip))
        except:
            pass
        
        return ips
    
    def is_ip_private(self, ip_addr):
        """Indicate if the given IP is private"""

        return ipaddress.ip_address(ip_addr).is_private
    
    def write_analysis(self, **kwargs):
        """After everything was found, create CSVs with some interesting data"""

        name = kwargs["name"]
        directory = kwargs["directory"]
        self.task_name = f"{name}_csvs"

        directory = f"{directory}/{name}"
        if not os.path.exists(directory):
            os.mkdir(directory)
        
        current_path = os.path.dirname(os.path.realpath(__file__))
        csv_queries_path = current_path + f"/../../intel/{name}/info/csv_queries.yaml"

        with open(csv_queries_path, "r") as f:
            queries = yaml.safe_load(f)["queries"]
        
        self._disc_loop(queries, self._write_csv, f"{name}_csvs", **{"directory": directory})
        self.progress.log(f"Final {name} analysis finished, written in {directory}")
    
    def _write_csv(self, q_info, **kwargs):
        """Perform and write each analysis"""

        directory = kwargs["directory"]
        q_name = q_info["name"]
        query = q_info["query"]
        res = graph.query(query)
        res_table : Table = res.to_table()
        with open(directory+"/"+q_name+".csv", "w") as f:
            res_table.write_separated_values(separator="|", file=f, header=True)
    
    def tool_exists(selt, tool_name) -> bool:
        """Check if a tool exists"""
        return which(tool_name) is not None
    
    def start_discovery(self, functions: list, writing_analysis=False):
        """Given a list of functions, initiate them"""
        threads = []
        for function, name, kwargs in functions:
            if not writing_analysis:
                self.logger.info(f"Enumerating {name}...")
            else:
                self.logger.info(f"Writting analysis of {name}...")

            threads.append(POOL.submit(function, **kwargs))
        
        while any(not t.done() for t in threads):
            time.sleep(5)
        
        for t in threads:
            t.result()

