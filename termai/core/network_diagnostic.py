"""Network Diagnostic AI"""

import subprocess
import re
from typing import Dict, Any, Optional, List
from .llm import LLMClient
from .display import DisplayManager
from .executor import CommandExecutor


class NetworkDiagnostic:
    """AI-powered network diagnostic tool"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize network diagnostic"""
        self.llm_client = llm_client or LLMClient()
        self.display = DisplayManager()
        self.executor = CommandExecutor()

    def ping(self, host: str, count: int = 4, explain: bool = True) -> Dict[str, Any]:
        """
        Ping a host and explain results
        
        Args:
            host: Hostname or IP address
            count: Number of ping packets
            explain: If True, provide AI explanation
            
        Returns:
            Ping results with explanation
        """
        self.display.console.print(f"[bold]🌐 Pinging:[/bold] [green]{host}[/green]")
        
        try:
            result = subprocess.run(
                f"ping -c {count} {host}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            error = result.stderr
            
            result_dict = {
                "host": host,
                "command": f"ping -c {count} {host}",
                "return_code": result.returncode,
                "output": output,
                "error": error,
                "success": result.returncode == 0
            }
            
            # Parse ping statistics
            stats = self._parse_ping_output(output)
            result_dict.update(stats)
            
            # AI explanation
            if explain:
                explanation = self._explain_ping_result(result_dict)
                result_dict["explanation"] = explanation
                self.display.console.print(f"\n[bold]📊 Results:[/bold]")
                self.display.console.print(explanation)
            
            return result_dict
            
        except subprocess.TimeoutExpired:
            return {
                "host": host,
                "success": False,
                "error": "Ping timed out",
                "explanation": "The ping request timed out. The host may be unreachable, firewall may be blocking, or network may be down."
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e)
            }

    def trace_route(self, host: str, explain: bool = True) -> Dict[str, Any]:
        """
        Trace route to a host and explain results
        
        Args:
            host: Hostname or IP address
            explain: If True, provide AI explanation
            
        Returns:
            Traceroute results with explanation
        """
        self.display.console.print(f"[bold]🛤️  Tracing route to:[/bold] [green]{host}[/green]")
        
        try:
            result = subprocess.run(
                f"traceroute {host}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout
            error = result.stderr
            
            result_dict = {
                "host": host,
                "command": f"traceroute {host}",
                "return_code": result.returncode,
                "output": output,
                "error": error,
                "success": result.returncode == 0
            }
            
            # AI explanation
            if explain:
                explanation = self._explain_traceroute_result(result_dict)
                result_dict["explanation"] = explanation
                self.display.console.print(f"\n[bold]📊 Route Analysis:[/bold]")
                self.display.console.print(explanation)
            
            return result_dict
            
        except subprocess.TimeoutExpired:
            return {
                "host": host,
                "success": False,
                "error": "Traceroute timed out"
            }
        except Exception as e:
            return {
                "host": host,
                "success": False,
                "error": str(e)
            }

    def check_port(self, host: str, port: int, explain: bool = True) -> Dict[str, Any]:
        """
        Check if a port is open on a host
        
        Args:
            host: Hostname or IP address
            port: Port number
            explain: If True, provide AI explanation
            
        Returns:
            Port check results with explanation
        """
        self.display.console.print(f"[bold]🔌 Checking port:[/bold] [green]{host}:{port}[/green]")
        
        try:
            # Try using nc (netcat) or telnet
            result = subprocess.run(
                f"timeout 3 bash -c '</dev/tcp/{host}/{port}' 2>&1 || nc -zv -w 3 {host} {port} 2>&1 || echo 'Port check failed'",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout + result.stderr
            is_open = "succeeded" in output.lower() or "open" in output.lower() or result.returncode == 0
            
            result_dict = {
                "host": host,
                "port": port,
                "command": f"nc -zv {host} {port}",
                "output": output,
                "is_open": is_open,
                "success": True
            }
            
            # AI explanation
            if explain:
                explanation = self._explain_port_result(result_dict)
                result_dict["explanation"] = explanation
                self.display.console.print(f"\n[bold]📊 Port Status:[/bold]")
                self.display.console.print(explanation)
            
            return result_dict
            
        except Exception as e:
            return {
                "host": host,
                "port": port,
                "success": False,
                "error": str(e)
            }

    def dns_lookup(self, hostname: str, explain: bool = True) -> Dict[str, Any]:
        """
        Perform DNS lookup and explain results
        
        Args:
            hostname: Hostname to lookup
            explain: If True, provide AI explanation
            
        Returns:
            DNS lookup results with explanation
        """
        self.display.console.print(f"[bold]🔍 DNS Lookup:[/bold] [green]{hostname}[/green]")
        
        try:
            result = subprocess.run(
                f"host {hostname}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout
            error = result.stderr
            
            # Also try dig if available
            if not output or result.returncode != 0:
                dig_result = subprocess.run(
                    f"dig {hostname} +short",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if dig_result.returncode == 0:
                    output = dig_result.stdout
                    result.returncode = 0
            
            result_dict = {
                "hostname": hostname,
                "command": f"host {hostname}",
                "return_code": result.returncode,
                "output": output,
                "error": error,
                "success": result.returncode == 0
            }
            
            # Parse DNS records
            if output:
                ip_addresses = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', output)
                result_dict["ip_addresses"] = ip_addresses
            
            # AI explanation
            if explain:
                explanation = self._explain_dns_result(result_dict)
                result_dict["explanation"] = explanation
                self.display.console.print(f"\n[bold]📊 DNS Information:[/bold]")
                self.display.console.print(explanation)
            
            return result_dict
            
        except Exception as e:
            return {
                "hostname": hostname,
                "success": False,
                "error": str(e)
            }

    def _parse_ping_output(self, output: str) -> Dict[str, Any]:
        """Parse ping output for statistics"""
        stats = {}
        
        # Extract packet loss
        loss_match = re.search(r'(\d+)% packet loss', output)
        if loss_match:
            stats["packet_loss"] = int(loss_match.group(1))
        
        # Extract timing stats
        time_match = re.search(r'min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
        if time_match:
            stats["min_time"] = float(time_match.group(1))
            stats["avg_time"] = float(time_match.group(2))
            stats["max_time"] = float(time_match.group(3))
            stats["mdev"] = float(time_match.group(4))
        
        return stats

    def _explain_ping_result(self, result: Dict[str, Any]) -> str:
        """Get AI explanation of ping results"""
        prompt = f"""Explain these ping results in simple terms:

Host: {result.get('host')}
Success: {result.get('success')}
Packet Loss: {result.get('packet_loss', 'N/A')}%
Average Time: {result.get('avg_time', 'N/A')}ms
Output: {result.get('output', '')[:500]}

Explain:
1. What the results mean
2. If there are any issues
3. What might cause problems
4. How to interpret the numbers"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a network diagnostic expert. Explain network test results clearly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"

    def _explain_traceroute_result(self, result: Dict[str, Any]) -> str:
        """Get AI explanation of traceroute results"""
        prompt = f"""Explain these traceroute results:

Host: {result.get('host')}
Output: {result.get('output', '')[:500]}

Explain:
1. The network path
2. Number of hops
3. Any issues or slow hops
4. What the results indicate"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a network diagnostic expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"

    def _explain_port_result(self, result: Dict[str, Any]) -> str:
        """Get AI explanation of port check results"""
        status = "OPEN" if result.get("is_open") else "CLOSED/FILTERED"
        
        prompt = f"""Explain this port check result:

Host: {result.get('host')}
Port: {result.get('port')}
Status: {status}
Output: {result.get('output', '')[:300]}

Explain:
1. What the status means
2. Why the port might be closed
3. What services typically use this port
4. How to troubleshoot"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a network security and diagnostic expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"

    def _explain_dns_result(self, result: Dict[str, Any]) -> str:
        """Get AI explanation of DNS lookup results"""
        prompt = f"""Explain these DNS lookup results:

Hostname: {result.get('hostname')}
IP Addresses: {result.get('ip_addresses', [])}
Success: {result.get('success')}
Output: {result.get('output', '')[:300]}

Explain:
1. What the DNS records mean
2. The IP addresses found
3. Any issues with the lookup
4. What this tells us about the hostname"""

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.config.get("model", "x-ai/grok-4.1-fast:free"),
                messages=[
                    {"role": "system", "content": "You are a DNS and network expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Could not generate explanation: {str(e)}"
