"""
Configuration Management
Loads templates from JSON and environment variables
"""

import os
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
from termcolor import colored


class TemplateConfig(BaseModel):
    """Configuration for a single invoice template"""
    generator_id: int
    subject_id: int
    due_days: int = 14
    description: Optional[str] = None


class AppConfig:
    """Application configuration singleton"""
    
    _instance: Optional["AppConfig"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._templates: Dict[str, TemplateConfig] = {}
        self._load_env()
        self._load_templates()
    
    def _load_env(self):
        """Load environment variables"""
        # Fakturoid API credentials
        self.FAKTUROID_CLIENT_ID = os.getenv("FAKTUROID_CLIENT_ID")
        self.FAKTUROID_CLIENT_SECRET = os.getenv("FAKTUROID_CLIENT_SECRET")
        self.FAKTUROID_ACCOUNT_SLUG = os.getenv("FAKTUROID_ACCOUNT_SLUG")
        self.USER_AGENT = os.getenv("USER_AGENT", "FakturoidBot (bot@example.com)")
        self.TEMPLATES_PATH = os.getenv("TEMPLATES_PATH", "/app/config/templates.json")
        
        # API Basic Auth credentials
        self.API_USERNAME = os.getenv("API_USERNAME")
        self.API_PASSWORD = os.getenv("API_PASSWORD")
        
        # Validate required env vars
        missing = []
        if not self.FAKTUROID_CLIENT_ID:
            missing.append("FAKTUROID_CLIENT_ID")
        if not self.FAKTUROID_CLIENT_SECRET:
            missing.append("FAKTUROID_CLIENT_SECRET")
        if not self.FAKTUROID_ACCOUNT_SLUG:
            missing.append("FAKTUROID_ACCOUNT_SLUG")
        if not self.API_USERNAME:
            missing.append("API_USERNAME")
        if not self.API_PASSWORD:
            missing.append("API_PASSWORD")
        
        if missing:
            print(colored(f"✗ Missing environment variables: {', '.join(missing)}", "red"))
    
    def _load_templates(self):
        """Load templates from JSON file"""
        try:
            # Try multiple paths for flexibility
            paths_to_try = [
                self.TEMPLATES_PATH,
                "config/templates.json",
                "./config/templates.json",
                "/app/config/templates.json"
            ]
            
            loaded = False
            for path in paths_to_try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    for name, config in data.items():
                        self._templates[name] = TemplateConfig(**config)
                    
                    print(colored(f"✓ Loaded {len(self._templates)} templates from {path}", "green"))
                    loaded = True
                    break
            
            if not loaded:
                print(colored(f"⚠ No templates file found, tried: {paths_to_try}", "yellow"))
                
        except json.JSONDecodeError as e:
            print(colored(f"✗ Invalid JSON in templates file: {e}", "red"))
        except Exception as e:
            print(colored(f"✗ Failed to load templates: {e}", "red"))
    
    def get_template(self, name: str) -> Optional[TemplateConfig]:
        """Get template configuration by name"""
        return self._templates.get(name)
    
    def list_templates(self) -> Dict[str, TemplateConfig]:
        """List all available templates"""
        return self._templates.copy()
    
    def reload_templates(self):
        """Reload templates from file"""
        self._templates.clear()
        self._load_templates()


def get_config() -> AppConfig:
    """Get the application configuration"""
    return AppConfig()
