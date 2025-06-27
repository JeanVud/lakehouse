"""Command registry for automatic command discovery and registration"""
import os
import importlib
import yaml
from typing import Dict, Optional
from commands.base_command import BaseCommand
from utils import logger

class CommandRegistry:
    def __init__(self):
        self._handlers: Dict[str, BaseCommand] = {}
        self._config = self._load_config()
        self._register_commands_from_config()
    
    def _load_config(self) -> dict:
        """Load command configuration from YAML file"""
        config_path = os.path.join(os.path.dirname(__file__), 'commands.yaml')
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"✅ Loaded command configuration from {config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"❌ Configuration file not found: {config_path}")
            return {"commands": {}}
        except yaml.YAMLError as e:
            logger.error(f"❌ Error parsing YAML configuration: {e}")
            return {"commands": {}}
    
    def _import_command_class(self, module_name: str, class_name: str) -> Optional[type]:
        """Dynamically import a command class"""
        try:
            module = importlib.import_module(f"commands.{module_name}")
            command_class = getattr(module, class_name)
            logger.info(f"✅ Imported {class_name} from {module_name}")
            return command_class
        except ImportError as e:
            logger.error(f"❌ Failed to import module {module_name}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"❌ Failed to import class {class_name} from {module_name}: {e}")
            return None
    
    def _register_commands_from_config(self):
        """Register all commands from configuration file"""
        commands_config = self._config.get("commands", {})
        
        for command_key, config in commands_config.items():
            try:
                # Get class name and file name from config
                class_name = config.get("class")
                file_name = config.get("file", "").replace(".py", "")
                
                if not class_name or not file_name:
                    logger.warning(f"⚠️ Missing class or file for command {command_key}")
                    continue
                
                # Import the command class
                command_class = self._import_command_class(file_name, class_name)
                if command_class:
                    # Create instance and register
                    handler = command_class()
                    self.register_command(command_key, handler)
                    logger.info(f"✅ Registered command: {command_key}")
                else:
                    logger.error(f"❌ Failed to register command: {command_key}")
                    
            except Exception as e:
                logger.error(f"❌ Error registering command {command_key}: {e}")
    
    def register_command(self, command_key: str, handler: BaseCommand):
        """Register a command handler"""
        self._handlers[command_key] = handler
        handler.command_name = command_key
    
    def get_handler(self, command_key: str) -> Optional[BaseCommand]:
        """Get command handler by key"""
        return self._handlers.get(command_key)
    
    def get_all_handlers(self) -> Dict[str, BaseCommand]:
        """Get all registered handlers"""
        return self._handlers.copy()
    
    def get_available_commands(self) -> list:
        """Get list of all available command keys"""
        return list(self._handlers.keys())
    
    def get_session_config(self, command_name: str) -> dict:
        """Get session configuration for a command from YAML"""
        commands_config = self._config.get("commands", {})
        return commands_config.get(command_name, {"needs_session": False, "timeout_minutes": 0})
    
    def needs_session(self, command_name: str) -> bool:
        """Check if a command needs a session"""
        config = self.get_session_config(command_name)
        return config.get("needs_session", False)
    
    def get_timeout_minutes(self, command_name: str) -> int:
        """Get session timeout in minutes for a command"""
        config = self.get_session_config(command_name)
        return config.get("timeout_minutes", 0)
    
    def get_command_name(self, command_key: str) -> str:
        """Get the actual command name (e.g., 'log-finance') from command key"""
        config = self.get_session_config(command_key)
        return config.get("command_name", command_key)
    
    def get_command_by_name(self, command_name: str) -> Optional[str]:
        """Get command key by command name (e.g., 'log-finance' -> 'log_finance')"""
        commands_config = self._config.get("commands", {})
        for key, config in commands_config.items():
            if config.get("command_name") == command_name:
                return key
        return None
    
    def get_all_commands(self) -> list:
        """Get list of all available command keys"""
        return list(self._config.get("commands", {}).keys())
    
    def validate_commands(self):
        """Validate that all configured commands have handlers"""
        config_commands = self.get_all_commands()
        registered_commands = self.get_available_commands()
        
        missing_commands = [cmd for cmd in config_commands if cmd not in registered_commands]
        if missing_commands:
            raise ValueError(f"Missing handlers for commands: {missing_commands}")
        
        logger.info(f"✅ All {len(registered_commands)} commands validated successfully")

# Global command registry instance
command_registry = CommandRegistry() 