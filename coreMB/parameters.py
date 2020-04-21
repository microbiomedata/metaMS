
from dataclasses import dataclass,field
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class WorkflowParameters:
    
    files_path: tuple = ()
    reference_file_path: str = ''
    output_directory: str = ''
    output_filename: str = ''
    output_type: str = 'csv'
