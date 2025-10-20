#!/usr/bin/env python3
"""
Batch processing script for LC metabolomics workflow
Processes all mzML files in staging directory using 5 cores
"""

import sys
import time
from pathlib import Path
import glob

# Add the metaMS module to the path
sys.path.insert(0, '/Users/heal742/LOCAL/05_NMDC/02_MetaMS/metams')

from metaMS.lcms_metabolomics_workflow import run_lcms_metabolomics_workflow

def check_corems_version():
    """Check and display CoreMS version"""
    try:
        import corems
        version = getattr(corems, '__version__', 'Unknown')
        print(f"📦 CoreMS version: {version}")
        return version
    except ImportError:
        print("⚠️  CoreMS not found")
        return "Not Found"
    except Exception as e:
        print(f"⚠️  Could not determine CoreMS version: {e}")
        return "Error"

def find_raw_and_mzml_files(directory):
    """Find all .raw and .mzML files in directory"""
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    
    # Look for .raw and .mzML files (case insensitive)
    files = []
    for pattern in ['*.raw', '*.RAW', '*.Raw', '*.mzML', '*.mzml', '*.MZML']:
        files.extend(directory.glob(pattern))
    
    return sorted(files)

def check_already_processed(input_files, output_directory):
    """
    Check which files have already been processed and filter them out
    
    Parameters
    ----------
    input_files : list of Path
        List of .raw/.mzML files to process
    output_directory : str or Path
        Output directory to check for existing results
        
    Returns
    -------
    tuple : (files_to_process, already_processed)
        files_to_process: list of Path objects for files that need processing
        already_processed: list of Path objects for files already processed
    """
    output_dir = Path(output_directory)
    files_to_process = []
    already_processed = []
    
    print("\n🔍 Checking for already processed files...")
    
    for input_file in input_files:
        # Expected output directory name (stem without extension + .corems)
        expected_output_dir = output_dir / f"{input_file.stem}.corems"
        
        # Check if the output directory exists
        if expected_output_dir.exists() and expected_output_dir.is_dir():
            # Check for key output files to confirm processing completed
            hdf5_file = expected_output_dir / f"{input_file.stem}.hdf5"
            csv_files = list(expected_output_dir.glob("*.csv"))
            
            if hdf5_file.exists() and len(csv_files) > 0:
                print(f"   ✅ Already processed: {input_file.name}")
                already_processed.append(input_file)
            else:
                print(f"   🔄 Incomplete processing found for: {input_file.name}")
                print(f"      Missing: {'HDF5 ' if not hdf5_file.exists() else ''}{'CSV files' if len(csv_files) == 0 else ''}")
                files_to_process.append(input_file)
        else:
            print(f"   🆕 Not processed: {input_file.name}")
            files_to_process.append(input_file)
    
    return files_to_process, already_processed

def batch_lcms_metabolomics():
    """Run LC metabolomics workflow on all .raw and .mzML files in staging directory"""
    
    overall_start = time.time()
    
    # Parameters
    input_directory = "/Users/heal742/LOCAL/staging_test"
    output_directory = "/Users/heal742/LOCAL/staging_processed/processed_EMP500_b2_test"
    corems_toml_path = "/Users/heal742/LOCAL/05_NMDC/02_MetaMS/data_processing/_emp_500_lcms_metabolomics/metadata/emp_lcms_metab_corems_params.toml"
    msp_file_path = "/Users/heal742/LOCAL/05_NMDC/02_MetaMS/metams/test_data/test_lcms_metab_data/20250407_database.msp"
    scan_translator_path = "/Users/heal742/LOCAL/05_NMDC/02_MetaMS/data_processing/_emp_500_lcms_metabolomics/metadata/emp500_scan_translator.toml"
    cores = 5
    
    print("=" * 80)
    print("🚀 BATCH LC METABOLOMICS WORKFLOW")
    print("=" * 80)
    print(f"📁 Input directory: {input_directory}")
    print(f"📂 Output directory: {output_directory}")
    print(f"⚙️  CoreMS TOML: {Path(corems_toml_path).name}")
    print(f"🗄️  MSP file: {Path(msp_file_path).name}")
    print(f"🔄 Scan translator: {Path(scan_translator_path).name}")
    print(f"🚀 Cores: {cores}")
    
    # Check CoreMS version
    print("\n📦 Checking CoreMS version...")
    check_corems_version()
    
    print("=" * 80)
    
    # Find all .raw and .mzML files
    print(f"🔍 Searching for .raw and .mzML files in: {input_directory}")
    try:
        all_input_files = find_raw_and_mzml_files(input_directory)
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        return False
    
    if not all_input_files:
        print(f"❌ ERROR: No .raw or .mzML files found in {input_directory}")
        return False
    
    # Separate by file type for reporting
    raw_files = [f for f in all_input_files if f.suffix.lower() == '.raw']
    mzml_files = [f for f in all_input_files if f.suffix.lower() in ['.mzml']]
    
    print(f"✅ Found {len(all_input_files)} files total:")
    print(f"   📊 .raw files: {len(raw_files)}")
    print(f"   📊 .mzML files: {len(mzml_files)}")
    
    # Create output directory if it doesn't exist
    print(f"\n📂 Creating output directory: {output_directory}")
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    # Check which files are already processed
    files_to_process, already_processed = check_already_processed(all_input_files, output_directory)
    
    # Summary of processing status
    print(f"\n📊 Processing Status Summary:")
    print(f"   🔍 Total files found: {len(all_input_files)}")
    print(f"   ✅ Already processed: {len(already_processed)}")
    print(f"   🆕 Need processing: {len(files_to_process)}")
    
    if len(already_processed) > 0:
        print(f"\n✅ Already processed files (skipping):")
        for i, file_path in enumerate(already_processed, 1):
            print(f"   {i:2d}. {file_path.name}")
    
    if len(files_to_process) == 0:
        print("\n🎉 All files have already been processed!")
        return True
    
    print(f"\n🆕 Files to process:")
    for i, file_path in enumerate(files_to_process, 1):
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        file_type = file_path.suffix.upper()
        print(f"   {i:2d}. {file_path.name} ({file_size_mb:.1f} MB) [{file_type}]")
    
    # Calculate total size of files to process
    total_size_gb = sum(f.stat().st_size for f in files_to_process) / (1024**3)
    print(f"📊 Total data size to process: {total_size_gb:.2f} GB")
    
    # File validation
    print("\n🔍 Validating required files...")
    required_files = [
        corems_toml_path,
        msp_file_path,
        scan_translator_path
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ ERROR: Required file does not exist: {file_path}")
            return False
    
    print("✅ All required files found")
    
    # Convert file paths to comma-separated string (as expected by the workflow)
    file_paths_str = ",".join(str(f) for f in files_to_process)
    
    # Estimate processing time for remaining files
    estimated_time_per_file = 8.5  # minutes, based on your debug run
    estimated_total_time = (len(files_to_process) * estimated_time_per_file) / cores
    print(f"⏱️  Estimated processing time: {estimated_total_time:.1f} minutes with {cores} cores")
    
    # Confirmation prompt
    print("\n" + "=" * 80)
    if len(already_processed) > 0:
        print(f"🔄 Will skip {len(already_processed)} already processed files")
    response = input(f"🤔 Process {len(files_to_process)} remaining files (.raw and .mzML) with {cores} cores? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Processing cancelled by user")
        return False
    
    print("🚀 Starting batch processing...")
    print("=" * 80)
    
    try:
        # Run the workflow only on files that need processing
        run_lcms_metabolomics_workflow(
            lcmsmetab_workflow_parameters_file=None,
            file_paths=file_paths_str,
            output_directory=output_directory,
            corems_toml_path=corems_toml_path,
            msp_file_path=msp_file_path,
            scan_translator_path=scan_translator_path,
            cores=cores,
        )
        
        overall_end = time.time()
        overall_duration = overall_end - overall_start
        
        print("\n" + "=" * 80)
        print("🎉 SUCCESS: Batch workflow completed!")
        print(f"⏱️  Total processing time: {overall_duration/60:.1f} minutes")
        print(f"📂 Check output in: {output_directory}")
        if len(files_to_process) > 0:
            print(f"📊 Average time per file: {(overall_duration/60)/len(files_to_process):.1f} minutes")
        print("=" * 80)
        
        # List output directories
        output_path = Path(output_directory)
        if output_path.exists():
            subdirs = [d for d in output_path.iterdir() if d.is_dir()]
            print(f"📁 Total output directories: {len(subdirs)}")
            
            # Count new vs existing
            newly_processed = len(files_to_process)
            print(f"   🆕 Newly processed: {newly_processed}")
            print(f"   ✅ Previously completed: {len(already_processed)}")
            
            # Show a few examples of output
            print(f"\n📦 Sample output directories:")
            for i, subdir in enumerate(sorted(subdirs)[:5]):
                csv_files = list(subdir.glob("*.csv"))
                hdf5_files = list(subdir.glob("*.hdf5"))
                print(f"   📦 {subdir.name} ({len(csv_files)} CSV, {len(hdf5_files)} HDF5)")
            if len(subdirs) > 5:
                print(f"   ... and {len(subdirs) - 5} more directories")
        
        return True
        
    except Exception as e:
        overall_end = time.time()
        overall_duration = overall_end - overall_start
        
        print("=" * 80)
        print(f"❌ ERROR: Batch workflow failed!")
        print(f"🔍 Exception type: {type(e).__name__}")
        print(f"💬 Exception message: {str(e)}")
        print(f"⏱️  Processing time before failure: {overall_duration/60:.1f} minutes")
        print("=" * 80)
        
        # Print full traceback for debugging
        import traceback
        print("\n📋 FULL TRACEBACK:")
        print("-" * 40)
        traceback.print_exc()
        
        return False

def main():
    """Main function"""
    print("🔬 Starting LC Metabolomics Batch Processing (.raw and .mzML files)")
    print(f"🐍 Python path includes: {sys.path[0]}")
    
    success = batch_lcms_metabolomics()
    
    if success:
        print("\n✅ Batch processing completed successfully!")
    else:
        print("\n❌ Batch processing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()