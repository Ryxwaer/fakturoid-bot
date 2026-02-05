"""
Fakturoid API Service
Handles OAuth authentication and API calls
"""

import sys
import base64
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from termcolor import colored

sys.stdout.reconfigure(encoding='utf-8')


class FakturoidService:
    """
    Fakturoid API v3 Service
    Uses OAuth Client Credentials Flow
    """
    
    BASE_URL = "https://app.fakturoid.cz/api/v3"
    TOKEN_EXPIRY_BUFFER = 300  # Refresh 5 minutes before expiry
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        account_slug: str,
        user_agent: str
    ):
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.ACCOUNT_SLUG = account_slug
        self.USER_AGENT = user_agent
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        print(colored("✓ FakturoidService initialized", "green"))
    
    def _get_basic_auth_header(self) -> str:
        """Create Basic Auth header for OAuth"""
        credentials = f"{self.CLIENT_ID}:{self.CLIENT_SECRET}"
        encoded = base64.urlsafe_b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _get_access_token(self) -> str:
        """Get or refresh OAuth access token"""
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(seconds=self.TOKEN_EXPIRY_BUFFER):
                return self._access_token
        
        print(colored("→ Obtaining new access token...", "yellow"))
        
        response = requests.post(
            f"{self.BASE_URL}/oauth/token",
            headers={
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": self._get_basic_auth_header()
            },
            json={"grant_type": "client_credentials"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(colored(f"✗ OAuth failed: {response.status_code}", "red"))
            raise Exception(f"OAuth token request failed: {response.text}")
        
        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 7200)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        print(colored(f"✓ Access token obtained (expires in {expires_in}s)", "green"))
        return self._access_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with Bearer token"""
        token = self._get_access_token()
        return {
            "User-Agent": self.USER_AGENT,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_generator(self, generator_id: int) -> Dict[str, Any]:
        """
        Fetch generator template with all line details
        Returns lines with unit_price, unit_name, vat_rate
        """
        url = f"{self.BASE_URL}/accounts/{self.ACCOUNT_SLUG}/generators/{generator_id}.json"
        
        print(colored(f"→ Fetching generator {generator_id}...", "cyan"))
        
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        
        if response.status_code != 200:
            print(colored(f"✗ Failed to get generator: {response.status_code}", "red"))
            raise Exception(f"Failed to get generator: {response.text}")
        
        data = response.json()
        print(colored(f"✓ Generator loaded: {data.get('name', 'Unknown')}", "green"))
        return data
    
    def create_invoice(
        self,
        generator_id: int,
        subject_id: int,
        lines: List[Dict[str, Any]],
        issued_on: str,
        due_days: int
    ) -> Dict[str, Any]:
        """
        Create invoice from generator with custom lines
        """
        url = f"{self.BASE_URL}/accounts/{self.ACCOUNT_SLUG}/invoices.json"
        
        payload = {
            "generator_id": generator_id,
            "subject_id": subject_id,
            "issued_on": issued_on,
            "due": due_days,
            "lines": lines
        }
        
        print(colored(f"→ Creating invoice (issued: {issued_on})...", "yellow"))
        
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            print(colored(f"✗ Failed to create invoice: {response.status_code}", "red"))
            raise Exception(f"Failed to create invoice: {response.text}")
        
        invoice = response.json()
        print(colored(f"✓ Invoice created: #{invoice.get('number')} (ID: {invoice.get('id')})", "green"))
        return invoice
    
    def download_invoice_pdf(self, invoice_id: int) -> bytes:
        """
        Download invoice as PDF bytes
        """
        url = f"{self.BASE_URL}/accounts/{self.ACCOUNT_SLUG}/invoices/{invoice_id}/download.pdf"
        
        headers = self._get_headers()
        headers["Accept"] = "application/pdf"
        
        print(colored(f"→ Downloading PDF for invoice {invoice_id}...", "yellow"))
        
        response = requests.get(url, headers=headers, timeout=60)
        
        if response.status_code != 200:
            print(colored(f"✗ Failed to download PDF: {response.status_code}", "red"))
            raise Exception(f"Failed to download PDF: {response.text}")
        
        print(colored(f"✓ PDF downloaded ({len(response.content)} bytes)", "green"))
        return response.content
    
    def build_invoice_lines(
        self,
        generator_lines: List[Dict[str, Any]],
        quantities: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Build invoice lines by matching quantities to generator template lines
        
        Args:
            generator_lines: Lines from generator with unit_price, unit_name, vat_rate
            quantities: Mapping of line names to quantities
        
        Returns:
            List of invoice lines ready for API
        """
        # Create lookup by line name
        template_lookup = {line["name"]: line for line in generator_lines}
        
        invoice_lines = []
        for name, quantity in quantities.items():
            if name not in template_lookup:
                available = list(template_lookup.keys())
                raise ValueError(f"Line '{name}' not found in generator. Available: {available}")
            
            template_line = template_lookup[name]
            invoice_lines.append({
                "name": name,
                "quantity": quantity,
                "unit_name": template_line.get("unit_name", ""),
                "unit_price": float(template_line.get("unit_price", 0)),
                "vat_rate": template_line.get("vat_rate", 0)
            })
        
        return invoice_lines


def get_last_day_of_previous_month() -> str:
    """Get last day of previous month in YYYY-MM-DD format"""
    first_of_current = datetime.now().replace(day=1)
    last_of_previous = first_of_current - timedelta(days=1)
    return last_of_previous.strftime("%Y-%m-%d")
