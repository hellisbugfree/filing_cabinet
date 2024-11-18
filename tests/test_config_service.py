"""Tests for ConfigService."""
import os
import tempfile
import pytest
import json
from filing_cabinet.config.config_service import ConfigService, ConfigurationError

@pytest.fixture
def temp_db():
    """Temporary database file."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def config_service(temp_db):
    """ConfigService instance."""
    service = ConfigService(temp_db)
    yield service
    service.close()

def test_singleton_pattern():
    """Test that ConfigService follows singleton pattern."""
    with tempfile.NamedTemporaryFile() as temp:
        service1 = ConfigService(temp.name)
        service2 = ConfigService(temp.name)
        assert service1 is service2

def test_create_get_config(config_service):
    """Test creating and getting configuration values."""
    # Create a new config entry
    config_service.create('test.key', 'test_value', 'default_value', 'Test description')
    
    # Get the value
    value = config_service.get('test.key')
    assert value == 'test_value'
    
    # Get with default for non-existent key
    value = config_service.get('non.existent', 'default')
    assert value == 'default'

def test_set_config(config_service):
    """Test setting configuration values."""
    # Create initial value
    config_service.create('test.key', 'initial_value')
    
    # Update the value
    config_service.set('test.key', 'new_value')
    
    # Verify the update
    value = config_service.get('test.key')
    assert value == 'new_value'

def test_list_all(config_service):
    """Test listing all configuration values."""
    # Create some config entries
    config_service.create('test.key1', 'value1', 'default1', 'Description 1')
    config_service.create('test.key2', 'value2', 'default2', 'Description 2')
    
    # List all configs
    configs = config_service.list_all()
    assert len(configs) == 2
    assert 'test.key1' in configs
    assert 'test.key2' in configs
    
    # Verify structure of config entries
    for key in ['test.key1', 'test.key2']:
        assert 'value' in configs[key]
        assert 'default' in configs[key]
        assert 'description' in configs[key]

def test_export_import(config_service, temp_db):
    """Test exporting and importing configuration."""
    # Create some config entries
    config_service.create('test.key1', 'value1', 'default1', 'Description 1')
    config_service.create('test.key2', 'value2', 'default2', 'Description 2')
    
    # Export to file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        config_service.export_to_file(temp.name)
        
        # Verify export file content
        with open(temp.name, 'r') as f:
            exported = json.load(f)
            assert len(exported) == 2
            assert 'test.key1' in exported
            assert 'test.key2' in exported
        
        # Create new config service and import
        new_service = ConfigService(temp_db)
        new_service.import_from_file(temp.name)
        
        # Verify imported values
        configs = new_service.list_all()
        assert len(configs) == 2
        assert configs['test.key1']['value'] == 'value1'
        assert configs['test.key2']['value'] == 'value2'
        
        os.unlink(temp.name)

def test_error_handling(config_service):
    """Test error handling."""
    # Test creating duplicate key
    config_service.create('test.key', 'value')
    with pytest.raises(ConfigurationError):
        config_service.create('test.key', 'new_value')
    
    # Test getting non-existent key without default
    assert config_service.get('non.existent') is None
