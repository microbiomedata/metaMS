workflow gcmsMetabolomics {
    
    Array[File] file_paths
    
    File calibration_file_path

    String output_directory

    String output_filename

    String output_type

    File corems_json_path

    call runMetaMS {
         input: data_dir=data_dir,
                calibration_file_path, calibration_file_path,
                output_directory, output_directory,
                output_filename, output_filename,
                output_type, output_type,
                corems_json_path, corems_json_path
    }
}

task runMetaMS {
    
    Array[File] file_paths
    
    File calibration_file_path

    String output_directory

    String output_filename

    String output_type

    File corems_json_path

    Int jobs_count
    
    command {

        run-gcms-wdl-workflow file_paths calibration_file_path output_directory output_filename output_type corems_json_path --jobs jobs_count
    }
    
    output {
        
        String out = read_string(stdout())
        File output_file = "${output_directory}/${output_filename}.${output_type}"
         
    }

    runtime {
        docker: "microbiomedata/metams:latest"
    
    }
}

