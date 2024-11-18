"""Tests for FileService."""
import os
import tempfile
import pytest
from pathlib import Path
from filing_cabinet.services.file_service import FileService
from filing_cabinet.models import File, Incarnation
from filing_cabinet.repositories import FileRepository, IncarnationRepository

@pytest.fixture
def temp_db():
    """Temporary database file."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def temp_file():
    """Temporary test file."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'test content')
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def file_service(temp_db):
    """FileService instance."""
    service = FileService(temp_db)
    yield service
    service.__del__()

def test_checkin_file(file_service, temp_file):
    """Test checking in a file."""
    checksum = file_service.checkin_file(temp_file)
    assert checksum is not None
    
    # Verify file was added
    file, incarnations = file_service.get_file_info(temp_file)
    assert file is not None
    assert len(incarnations) == 1
    assert incarnations[0].path == temp_file

def test_checkout_file(file_service, temp_file):
    """Test checking out a file."""
    # First check in the file
    checksum = file_service.checkin_file(temp_file)
    
    # Then check it out to a new location
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'checkout.txt')
        result_path = file_service.checkout_file(checksum, output_path)
        
        assert result_path is not None
        assert os.path.exists(result_path)
        with open(result_path, 'rb') as f:
            assert f.read() == b'test content'

def test_index_files(file_service):
    """Test indexing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        test_files = []
        for i in range(3):
            path = os.path.join(temp_dir, f'test{i}.txt')
            with open(path, 'w') as f:
                f.write(f'content {i}')
            test_files.append(path)
        
        # Index the directory
        indexed = file_service.index_files(temp_dir)
        assert len(indexed) == 3
        
        # Verify all files were indexed
        for path in test_files:
            file, incarnations = file_service.get_file_info(path)
            assert file is not None
            assert len(incarnations) == 1
            assert incarnations[0].path == path

def test_get_statistics(file_service, temp_file):
    """Test getting statistics."""
    # Add a file first
    file_service.checkin_file(temp_file)
    
    stats = file_service.get_statistics()
    assert stats['total_files'] == 1
    assert stats['total_incarnations'] == 1
    assert 'name' in stats
    assert 'version' in stats
