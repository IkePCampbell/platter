#!/usr/bin/env python3
"""
Platter - A comprehensive CLI tool for Jenkins automation
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

import jenkins
import requests
import tabulate
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class Platter:
    def __init__(self):
        self.jenkins_url = os.environ.get('JENKINS_URL')
        self.username = os.environ.get('JENKINS_USERNAME') or os.environ.get('USERNAME')
        self.api_key = os.environ.get('JENKINS_API_KEY')
        
        if not all([self.jenkins_url, self.username, self.api_key]):
            print(f"{Fore.RED}Error: Missing environment variables.{Style.RESET_ALL}")
            print("Please set the following environment variables:")
            print("  - JENKINS_URL: Your Jenkins server URL")
            print("  - JENKINS_USERNAME: Your Jenkins username")
            print("  - JENKINS_API_KEY: Your Jenkins API token")
            sys.exit(1)
            
        try:
            self.server = jenkins.Jenkins(
                self.jenkins_url,
                username=self.username,
                password=self.api_key
            )
            # Test connection
            self.user = self.server.get_whoami()
            self.version = self.server.get_version()
        except Exception as e:
            print(f"{Fore.RED}Error connecting to Jenkins: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def list_jobs(self, path: str, show_status: bool = False, filter_status: Optional[str] = None) -> None:
        """
        List Jenkins jobs with optional status filtering
        
        Args:
            path: Path to list jobs from (use '/' for root)
            show_status: Whether to show job status
            filter_status: Filter jobs by status (success, failure, unstable, disabled, etc.)
        """
        depth = 0 if path == '/' else 5
        jobs = self.server.get_jobs(folder_depth=depth)
        
        headers = ["Type", "Name", "Path"]
        if show_status:
            headers.extend(["Status", "Last Build", "Duration"])
            
        rows = []
        
        for job in jobs:
            if path in job['fullname'] or depth == 0:
                job_type = "📁 Folder" if job['_class'] == "com.cloudbees.hudson.plugins.folder.Folder" else "🔧 Job"
                name = job['name']
                fullname = job['fullname']
                
                row = [job_type, name, fullname]
                
                if show_status and job_type != "📁 Folder":
                    try:
                        job_info = self.server.get_job_info(fullname)
                        last_build = job_info.get('lastBuild', {})
                        
                        if last_build:
                            build_number = last_build.get('number')
                            if build_number:
                                build_info = self.server.get_build_info(fullname, build_number)
                                status = build_info.get('result', 'UNKNOWN')
                                
                                # Apply color based on status
                                if status == 'SUCCESS':
                                    status = f"{Fore.GREEN}SUCCESS{Style.RESET_ALL}"
                                elif status == 'FAILURE':
                                    status = f"{Fore.RED}FAILURE{Style.RESET_ALL}"
                                elif status == 'UNSTABLE':
                                    status = f"{Fore.YELLOW}UNSTABLE{Style.RESET_ALL}"
                                elif status == 'ABORTED':
                                    status = f"{Fore.MAGENTA}ABORTED{Style.RESET_ALL}"
                                
                                timestamp = datetime.fromtimestamp(build_info.get('timestamp', 0)/1000)
                                duration = f"{build_info.get('duration', 0)/1000:.1f}s"
                                
                                row.extend([status, timestamp.strftime('%Y-%m-%d %H:%M'), duration])
                            else:
                                row.extend(["N/A", "Never built", "N/A"])
                        else:
                            row.extend(["N/A", "Never built", "N/A"])
                    except Exception:
                        row.extend(["ERROR", "Failed to fetch", "N/A"])
                
                # Apply filter if specified
                if filter_status and show_status:
                    if filter_status.upper() not in row[3]:
                        continue
                        
                rows.append(row)
        
        if rows:
            print(tabulate.tabulate(rows, headers=headers, tablefmt="pretty"))
        else:
            print(f"{Fore.YELLOW}No jobs found matching the criteria.{Style.RESET_ALL}")

    def get_branch(self, job_path: str) -> str:
        """
        Get the SCM branch for a job
        
        Args:
            job_path: Path to the Jenkins job
            
        Returns:
            Branch name
        """
        try:
            config = self.server.get_job_config(job_path)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(config)
            
            # Try to find branch in different job types
            branch_paths = [
                'definition/scm/branches/hudson.plugins.git.BranchSpec/name',
                'scm/branches/hudson.plugins.git.BranchSpec/name'
            ]
            
            for path in branch_paths:
                elements = path.split('/')
                node = root
                for element in elements:
                    found = node.find(element)
                    if found is None:
                        break
                    node = found
                else:
                    if node.text:
                        print(f"Branch: {Fore.CYAN}{node.text}{Style.RESET_ALL}")
                        return node.text
            
            print(f"{Fore.YELLOW}No branch configuration found for this job.{Style.RESET_ALL}")
            return ""
        except Exception as e:
            print(f"{Fore.RED}Error getting branch: {e}{Style.RESET_ALL}")
            return ""

    def replace_branch(self, job_path: str, new_branch: str) -> None:
        """
        Replace the SCM branch for a job
        
        Args:
            job_path: Path to the Jenkins job
            new_branch: New branch name (will be prefixed with '*/' if not already)
        """
        try:
            config = self.server.get_job_config(job_path)
            old_branch = self.get_branch(job_path)
            
            if not old_branch:
                return
                
            # Add '*/' prefix if not present
            if not new_branch.startswith('*/'):
                new_branch = f'*/{new_branch}'
                
            new_config = config.replace(old_branch, new_branch)
            
            if new_config == config:
                print(f"{Fore.YELLOW}No changes made. Branch might already be set to {new_branch}{Style.RESET_ALL}")
                return
                
            self.server.reconfig_job(job_path, new_config)
            print(f"{Fore.GREEN}Successfully updated branch from {old_branch} to {new_branch}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error replacing branch: {e}{Style.RESET_ALL}")

    def build_job(self, job_path: str, parameters: Optional[Dict[str, Any]] = None, wait: bool = False) -> None:
        """
        Build a Jenkins job with optional parameters
        
        Args:
            job_path: Path to the Jenkins job
            parameters: Build parameters
            wait: Whether to wait for build completion
        """
        try:
            queue_id = self.server.build_job(job_path, parameters=parameters or {})
            print(f"{Fore.GREEN}Build triggered for {job_path} (Queue ID: {queue_id}){Style.RESET_ALL}")
            
            if wait:
                print("Waiting for build to start...")
                build_number = None
                
                # Wait for the build to start
                while build_number is None:
                    time.sleep(1)
                    queue_info = self.server.get_queue_item(queue_id)
                    if queue_info.get('executable'):
                        build_number = queue_info['executable']['number']
                        break
                
                print(f"Build #{build_number} started. Waiting for completion...")
                
                # Wait for the build to complete
                while True:
                    build_info = self.server.get_build_info(job_path, build_number)
                    if build_info.get('building') is False:
                        result = build_info.get('result')
                        duration = f"{build_info.get('duration', 0)/1000:.1f}s"
                        
                        if result == 'SUCCESS':
                            print(f"{Fore.GREEN}Build #{build_number} completed successfully in {duration}{Style.RESET_ALL}")
                        elif result == 'FAILURE':
                            print(f"{Fore.RED}Build #{build_number} failed in {duration}{Style.RESET_ALL}")
                        elif result == 'UNSTABLE':
                            print(f"{Fore.YELLOW}Build #{build_number} is unstable (completed in {duration}){Style.RESET_ALL}")
                        else:
                            print(f"Build #{build_number} completed with result: {result} in {duration}")
                        break
                    
                    time.sleep(5)
        except Exception as e:
            print(f"{Fore.RED}Error building job: {e}{Style.RESET_ALL}")

    def get_build_logs(self, job_path: str, build_number: Optional[int] = None) -> None:
        """
        Get build logs for a job
        
        Args:
            job_path: Path to the Jenkins job
            build_number: Build number (latest if None)
        """
        try:
            if build_number is None:
                job_info = self.server.get_job_info(job_path)
                last_build = job_info.get('lastBuild')
                if not last_build:
                    print(f"{Fore.YELLOW}No builds found for {job_path}{Style.RESET_ALL}")
                    return
                build_number = last_build['number']
            
            console_output = self.server.get_build_console_output(job_path, build_number)
            print(f"\n{Fore.CYAN}=== Build #{build_number} Console Output ==={Style.RESET_ALL}\n")
            print(console_output)
        except Exception as e:
            print(f"{Fore.RED}Error getting build logs: {e}{Style.RESET_ALL}")

    def get_job_config(self, job_path: str, output_file: Optional[str] = None) -> None:
        """
        Get the XML configuration for a job
        
        Args:
            job_path: Path to the Jenkins job
            output_file: File to save the configuration to
        """
        try:
            config = self.server.get_job_config(job_path)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(config)
                print(f"{Fore.GREEN}Configuration saved to {output_file}{Style.RESET_ALL}")
            else:
                print(config)
        except Exception as e:
            print(f"{Fore.RED}Error getting job configuration: {e}{Style.RESET_ALL}")

    def update_job_config(self, job_path: str, config_file: str) -> None:
        """
        Update the XML configuration for a job
        
        Args:
            job_path: Path to the Jenkins job
            config_file: File containing the new configuration
        """
        try:
            with open(config_file, 'r') as f:
                new_config = f.read()
                
            self.server.reconfig_job(job_path, new_config)
            print(f"{Fore.GREEN}Configuration updated for {job_path}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error updating job configuration: {e}{Style.RESET_ALL}")

    def create_job(self, job_name: str, config_file: str) -> None:
        """
        Create a new Jenkins job
        
        Args:
            job_name: Name for the new job
            config_file: File containing the job configuration
        """
        try:
            with open(config_file, 'r') as f:
                config = f.read()
                
            self.server.create_job(job_name, config)
            print(f"{Fore.GREEN}Job {job_name} created successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error creating job: {e}{Style.RESET_ALL}")

    def copy_job(self, source_job: str, target_job: str) -> None:
        """
        Copy a Jenkins job
        
        Args:
            source_job: Source job path
            target_job: Target job name
        """
        try:
            self.server.copy_job(source_job, target_job)
            print(f"{Fore.GREEN}Job {source_job} copied to {target_job}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error copying job: {e}{Style.RESET_ALL}")

    def delete_job(self, job_path: str, confirm: bool = True) -> None:
        """
        Delete a Jenkins job
        
        Args:
            job_path: Path to the Jenkins job
            confirm: Whether to ask for confirmation
        """
        try:
            if confirm:
                response = input(f"Are you sure you want to delete {job_path}? (y/N): ")
                if response.lower() != 'y':
                    print("Operation cancelled.")
                    return
                    
            self.server.delete_job(job_path)
            print(f"{Fore.GREEN}Job {job_path} deleted successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error deleting job: {e}{Style.RESET_ALL}")

    def enable_job(self, job_path: str) -> None:
        """
        Enable a Jenkins job
        
        Args:
            job_path: Path to the Jenkins job
        """
        try:
            self.server.enable_job(job_path)
            print(f"{Fore.GREEN}Job {job_path} enabled{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error enabling job: {e}{Style.RESET_ALL}")

    def disable_job(self, job_path: str) -> None:
        """
        Disable a Jenkins job
        
        Args:
            job_path: Path to the Jenkins job
        """
        try:
            self.server.disable_job(job_path)
            print(f"{Fore.GREEN}Job {job_path} disabled{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error disabling job: {e}{Style.RESET_ALL}")

    def get_plugins(self, output_file: Optional[str] = None) -> None:
        """
        List installed Jenkins plugins
        
        Args:
            output_file: File to save the plugin list to
        """
        try:
            plugins = self.server.get_plugins_info()
            
            headers = ["Name", "Version", "Enabled", "Long Name"]
            rows = []
            
            for plugin in plugins:
                rows.append([
                    plugin['shortName'],
                    plugin['version'],
                    "✅" if plugin['enabled'] else "❌",
                    plugin['longName']
                ])
                
            table = tabulate.tabulate(rows, headers=headers, tablefmt="pretty")
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(table)
                print(f"{Fore.GREEN}Plugin list saved to {output_file}{Style.RESET_ALL}")
            else:
                print(table)
        except Exception as e:
            print(f"{Fore.RED}Error getting plugins: {e}{Style.RESET_ALL}")

    def get_nodes(self) -> None:
        """List all Jenkins nodes/agents"""
        try:
            nodes = self.server.get_nodes()
            
            headers = ["Name", "Status", "Executors"]
            rows = []
            
            for node in nodes:
                name = node['name']
                if name == "":
                    name = "master"
                    
                # Get node info for additional details
                node_info = self.server.get_node_info(name)
                
                status = "Online" if not node_info.get('offline', False) else "Offline"
                if status == "Online":
                    status = f"{Fore.GREEN}Online{Style.RESET_ALL}"
                else:
                    status = f"{Fore.RED}Offline{Style.RESET_ALL}"
                    
                executors = node_info.get('numExecutors', 0)
                
                rows.append([name, status, executors])
                
            print(tabulate.tabulate(rows, headers=headers, tablefmt="pretty"))
        except Exception as e:
            print(f"{Fore.RED}Error getting nodes: {e}{Style.RESET_ALL}")

    def get_queue(self) -> None:
        """List queued builds"""
        try:
            queue_info = self.server.get_queue_info()
            
            if not queue_info:
                print(f"{Fore.YELLOW}Build queue is empty{Style.RESET_ALL}")
                return
                
            headers = ["ID", "Name", "Why Blocked", "In Queue Since"]
            rows = []
            
            for item in queue_info:
                queue_id = item['id']
                name = item['task']['name']
                why = item.get('why', 'N/A')
                since = datetime.fromtimestamp(item['inQueueSince']/1000).strftime('%Y-%m-%d %H:%M:%S')
                
                rows.append([queue_id, name, why, since])
                
            print(tabulate.tabulate(rows, headers=headers, tablefmt="pretty"))
        except Exception as e:
            print(f"{Fore.RED}Error getting queue: {e}{Style.RESET_ALL}")

    def cancel_queue(self, queue_id: int) -> None:
        """
        Cancel a queued build
        
        Args:
            queue_id: Queue item ID
        """
        try:
            self.server.cancel_queue(queue_id)
            print(f"{Fore.GREEN}Cancelled queue item {queue_id}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error cancelling queue item: {e}{Style.RESET_ALL}")

    def system_info(self) -> None:
        """Display Jenkins system information"""
        try:
            # Get system info using Jenkins API
            url = f"{self.jenkins_url}/api/json"
            response = requests.get(
                url,
                auth=(self.username, self.api_key),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                print(f"{Fore.RED}Error: Failed to get system info (Status code: {response.status_code}){Style.RESET_ALL}")
                return
                
            data = response.json()
            
            print(f"\n{Fore.CYAN}=== Jenkins System Information ==={Style.RESET_ALL}\n")
            print(f"URL:                 {self.jenkins_url}")
            print(f"Version:             {self.version}")
            print(f"Connected as:        {self.user['fullName']} ({self.username})")
            print(f"Mode:                {data.get('mode', 'Unknown')}")
            print(f"Node Description:    {data.get('nodeDescription', 'Unknown')}")
            print(f"Quiet Period:        {data.get('quietingDown', False)}")
            print(f"Slave Agent Port:    {data.get('slaveAgentPort', 'Unknown')}")
            print(f"CSRF Protection:     {data.get('useCrumbs', False)}")
            print(f"Views:               {len(data.get('views', []))}")
            print(f"Primary View:        {data.get('primaryView', {}).get('name', 'Unknown')}")
            
            # Get executor info
            executor_count = 0
            busy_executors = 0
            
            for computer in data.get('computers', []):
                executor_count += computer.get('numExecutors', 0)
                busy_executors += len([e for e in computer.get('executors', []) if e.get('busy', False)])
                
            print(f"Total Executors:     {executor_count}")
            print(f"Busy Executors:      {busy_executors}")
            print(f"Idle Executors:      {executor_count - busy_executors}")
        except Exception as e:
            print(f"{Fore.RED}Error getting system info: {e}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(
        description="Platter - A comprehensive CLI tool for Jenkins automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  platter list-jobs /                          # List all jobs in the root folder
  platter list-jobs /path --status             # List jobs with status
  platter list-jobs /path --status --filter success  # List only successful jobs
  platter get-branch "my job"                  # Get the SCM branch for a job
  platter replace-branch "my job" feature/xyz  # Update the SCM branch
  platter build "my job"                       # Trigger a build
  platter build "my job" --wait               # Trigger a build and wait for completion
  platter logs "my job"                       # Get logs for the latest build
  platter logs "my job" --build 123           # Get logs for build #123
  platter config-get "my job"                 # Get job configuration
  platter config-get "my job" --output job.xml # Save job configuration to file
  platter config-update "my job" job.xml      # Update job configuration
  platter create "my new job" job.xml         # Create a new job
  platter copy "source job" "target job"      # Copy a job
  platter delete "my job"                     # Delete a job (with confirmation)
  platter enable "my job"                     # Enable a job
  platter disable "my job"                    # Disable a job
  platter plugins                              # List installed plugins
  platter nodes                                # List all nodes/agents
  platter queue                                # List queued builds
  platter cancel-queue 123                     # Cancel a queued build
  platter info                                 # Display system information
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # list-jobs command
    list_parser = subparsers.add_parser('list-jobs', help='List Jenkins jobs')
    list_parser.add_argument('path', help='Path to list jobs from (use "/" for root)')
    list_parser.add_argument('--status', action='store_true', help='Show job status')
    list_parser.add_argument('--filter', help='Filter jobs by status (success, failure, etc.)')
    
    # get-branch command
    get_branch_parser = subparsers.add_parser('get-branch', help='Get SCM branch for a job')
    get_branch_parser.add_argument('job_path', help='Path to the Jenkins job')
    
    # replace-branch command
    replace_branch_parser = subparsers.add_parser('replace-branch', help='Replace SCM branch for a job')
    replace_branch_parser.add_argument('job_path', help='Path to the Jenkins job')
    replace_branch_parser.add_argument('new_branch', help='New branch name')
    
    # build command
    build_parser = subparsers.add_parser('build', help='Build a Jenkins job')
    build_parser.add_argument('job_path', help='Path to the Jenkins job')
    build_parser.add_argument('--params', help='Build parameters in JSON format')
    build_parser.add_argument('--wait', action='store_true', help='Wait for build completion')
    
    # logs command
    logs_parser = subparsers.add_parser('logs', help='Get build logs')
    logs_parser.add_argument('job_path', help='Path to the Jenkins job')
    logs_parser.add_argument('--build', type=int, help='Build number (latest if not specified)')
    
    # config-get command
    config_get_parser = subparsers.add_parser('config-get', help='Get job configuration')
    config_get_parser.add_argument('job_path', help='Path to the Jenkins job')
    config_get_parser.add_argument('--output', help='File to save the configuration to')
    
    # config-update command
    config_update_parser = subparsers.add_parser('config-update', help='Update job configuration')
    config_update_parser.add_argument('job_path', help='Path to the Jenkins job')
    config_update_parser.add_argument('config_file', help='File containing the new configuration')
    
    # create command
    create_parser = subparsers.add_parser('create', help='Create a new Jenkins job')
    create_parser.add_argument('job_name', help='Name for the new job')
    create_parser.add_argument('config_file', help='File containing the job configuration')
    
    # copy command
    copy_parser = subparsers.add_parser('copy', help='Copy a Jenkins job')
    copy_parser.add_argument('source_job', help='Source job path')
    copy_parser.add_argument('target_job', help='Target job name')
    
    # delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a Jenkins job')
    delete_parser.add_argument('job_path', help='Path to the Jenkins job')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # enable command
    enable_parser = subparsers.add_parser('enable', help='Enable a Jenkins job')
    enable_parser.add_argument('job_path', help='Path to the Jenkins job')
    
    # disable command
    disable_parser = subparsers.add_parser('disable', help='Disable a Jenkins job')
    disable_parser.add_argument('job_path', help='Path to the Jenkins job')
    
    # plugins command
    plugins_parser = subparsers.add_parser('plugins', help='List installed plugins')
    plugins_parser.add_argument('--output', help='File to save the plugin list to')
    
    # nodes command
    subparsers.add_parser('nodes', help='List all nodes/agents')
    
    # queue command
    subparsers.add_parser('queue', help='List queued builds')
    
    # cancel-queue command
    cancel_queue_parser = subparsers.add_parser('cancel-queue', help='Cancel a queued build')
    cancel_queue_parser.add_argument('queue_id', type=int, help='Queue item ID')
    
    # info command
    subparsers.add_parser('info', help='Display system information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    platter = Platter()
    
    if args.command == 'list-jobs':
        platter.list_jobs(args.path, args.status, args.filter)
    elif args.command == 'get-branch':
        platter.get_branch(args.job_path)
    elif args.command == 'replace-branch':
        platter.replace_branch(args.job_path, args.new_branch)
    elif args.command == 'build':
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                print(f"{Fore.RED}Error: Invalid JSON format for parameters{Style.RESET_ALL}")
                return
        platter.build_job(args.job_path, params, args.wait)
    elif args.command == 'logs':
        platter.get_build_logs(args.job_path, args.build)
    elif args.command == 'config-get':
        platter.get_job_config(args.job_path, args.output)
    elif args.command == 'config-update':
        platter.update_job_config(args.job_path, args.config_file)
    elif args.command == 'create':
        platter.create_job(args.job_name, args.config_file)
    elif args.command == 'copy':
        platter.copy_job(args.source_job, args.target_job)
    elif args.command == 'delete':
        platter.delete_job(args.job_path, not args.force)
    elif args.command == 'enable':
        platter.enable_job(args.job_path)
    elif args.command == 'disable':
        platter.disable_job(args.job_path)
    elif args.command == 'plugins':
        platter.get_plugins(args.output)
    elif args.command == 'nodes':
        platter.get_nodes()
    elif args.command == 'queue':
        platter.get_queue()
    elif args.command == 'cancel-queue':
        platter.cancel_queue(args.queue_id)
    elif args.command == 'info':
        platter.system_info()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(1)
