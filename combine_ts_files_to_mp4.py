import ffmpeg
import os
import glob
import tempfile
from pathlib import Path

def combine_ts_files_to_mp4(input_source, output_file, pattern="*.ts"):
    """
    Combine multiple .ts files into a single MP4 file with H.264 encoding
    
    Args:
        input_source (str or list): Directory containing .ts files, path to file list, or list of file paths
        output_file (str): Output MP4 file path
        pattern (str): File pattern to match (default: "*.ts") - ignored if input_source is list or file list
    """
    
    # Get list of .ts files based on input type
    if isinstance(input_source, list):
        ts_files = input_source.copy()  # Create a copy to avoid modifying original
        print(f"Using provided array of {len(ts_files)} files")
        
        # Validate that all files exist
        valid_files = []
        for i, file_path in enumerate(ts_files):
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                print(f"Warning: File not found (index {i}): {file_path}")
                return False
        ts_files = valid_files
        
    elif isinstance(input_source, str) and input_source.endswith('.txt'):
        ts_files = read_file_list(input_source)
        print(f"Loaded {len(ts_files)} files from file list")
    else:
        # Get all .ts files and sort them
        ts_files = glob.glob(os.path.join(input_source, pattern))
        ts_files.sort()  # Sort to ensure correct order
        print(f"Found {len(ts_files)} .ts files in directory")
    
    if not ts_files:
        if isinstance(input_source, list):
            print("No valid files found in provided array")
            return False
        elif isinstance(input_source, str) and input_source.endswith('.txt'):
            print(f"No .ts files found in file list {input_source}")
            return False
        else:
            print(f"No .ts files found in directory {input_source}")
            return False
    
    # Method 1: Using concat demuxer (fastest, no re-encoding)
    try:
        # Create a temporary file list for concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            concat_file = f.name
            for ts_file in ts_files:
                # Use absolute paths and escape special characters
                abs_path = os.path.abspath(ts_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        # Use concat demuxer for fast concatenation
        (
            ffmpeg
            .input(concat_file, format='concat', safe=0)
            .output(
                output_file,
                vcodec='libx264',
                acodec='aac',
                preset='medium',
                crf=23
            )
            .overwrite_output()
            .run(quiet=False)
        )
        
        # Clean up temporary file
        os.unlink(concat_file)
        print(f"Successfully created {output_file}")
        
    except Exception as e:
        print(f"Concat method failed: {e}")
        print("Trying alternative method...")
        
        # Method 2: Alternative approach using filter_complex
        try:
            # For very large numbers of files, process in batches
            batch_size = 100
            temp_files = []
            
            for i in range(0, len(ts_files), batch_size):
                batch = ts_files[i:i + batch_size]
                temp_output = f"temp_batch_{i//batch_size}.mp4"
                
                # Create input streams
                inputs = [ffmpeg.input(f) for f in batch]
                
                # Concatenate batch
                (
                    ffmpeg
                    .concat(*inputs, v=1, a=1)
                    .output(
                        temp_output,
                        vcodec='libx264',
                        acodec='aac',
                        preset='medium',
                        crf=23
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                temp_files.append(temp_output)
                print(f"Processed batch {i//batch_size + 1}")
            
            # If multiple batches, combine them
            if len(temp_files) > 1:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    final_concat_file = f.name
                    for temp_file in temp_files:
                        abs_path = os.path.abspath(temp_file).replace('\\', '/')
                        f.write(f"file '{abs_path}'\n")
                
                (
                    ffmpeg
                    .input(final_concat_file, format='concat', safe=0)
                    .output(
                        output_file,
                        vcodec='copy',  # No re-encoding needed
                        acodec='copy'
                    )
                    .overwrite_output()
                    .run(quiet=False)
                )
                
                # Clean up
                os.unlink(final_concat_file)
                for temp_file in temp_files:
                    os.remove(temp_file)
            else:
                # Only one batch, rename it
                os.rename(temp_files[0], output_file)
            
            print(f"Successfully created {output_file}")
            return True
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")
            return False

def read_file_list(file_list_path):
    """
    Read file paths from a text file
    
    Args:
        file_list_path (str): Path to file containing list of .ts files
        
    Returns:
        list: List of file paths
        
    File format examples:
        - One file per line: /path/to/file1.ts
        - With 'file' prefix: file '/path/to/file1.ts'
        - Relative or absolute paths supported
    """
    ts_files = []
    
    try:
        with open(file_list_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Handle different file list formats
                if line.startswith("file '") and line.endswith("'"):
                    # FFmpeg concat format: file '/path/to/file.ts'
                    file_path = line[6:-1]  # Remove "file '" and "'"
                elif line.startswith("file ") and (line.startswith("file '") or line.startswith('file "')):
                    # Handle quoted paths
                    quote_char = line[5]  # Get quote character
                    file_path = line[6:-1] if line.endswith(quote_char) else line[6:]
                else:
                    # Plain file path
                    file_path = line
                
                # Convert relative paths to absolute if needed
                if not os.path.isabs(file_path):
                    # Make relative to the file list's directory
                    base_dir = os.path.dirname(os.path.abspath(file_list_path))
                    file_path = os.path.join(base_dir, file_path)
                
                # Verify file exists
                if os.path.exists(file_path):
                    ts_files.append(file_path)
                else:
                    print(f"Warning: File not found (line {line_num}): {file_path}")
    
    except FileNotFoundError:
        raise FileNotFoundError(f"File list not found: {file_list_path}")
    except Exception as e:
        raise Exception(f"Error reading file list {file_list_path}: {e}")
    
    return ts_files

def create_file_list(directory, output_list_file, pattern="*.ts", format_type="simple"):
    """
    Create a file list from directory contents
    
    Args:
        directory (str): Directory containing .ts files
        output_list_file (str): Output file list path
        pattern (str): File pattern to match
        format_type (str): "simple" for plain paths, "ffmpeg" for concat format
    """
    ts_files = sorted(glob.glob(os.path.join(directory, pattern)))
    
    if not ts_files:
        raise ValueError(f"No files found matching pattern {pattern} in {directory}")
    
    with open(output_list_file, 'w', encoding='utf-8') as f:
        if format_type == "ffmpeg":
            f.write("# FFmpeg concat file list\n")
            f.write("# Generated automatically\n\n")
            for ts_file in ts_files:
                abs_path = os.path.abspath(ts_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        else:
            f.write("# Simple file list\n")
            f.write("# One file per line\n\n")
            for ts_file in ts_files:
                f.write(f"{os.path.abspath(ts_file)}\n")
    
    print(f"Created file list with {len(ts_files)} files: {output_list_file}")
    return output_list_file
    """
    Simple version for smaller number of files
    """
    ts_files = sorted(glob.glob(os.path.join(input_directory, "*.ts")))
    
    if not ts_files:
        raise ValueError(f"No .ts files found in {input_directory}")
    
    print(f"Combining {len(ts_files)} files...")
    
    # Create input streams
    inputs = [ffmpeg.input(f) for f in ts_files]
    
    # Concatenate all files
    (
        ffmpeg
        .concat(*inputs, v=1, a=1)
        .output(
            output_file,
            vcodec='libx264',
            acodec='aac',
            preset='medium',
            crf=23,
            movflags='faststart'  # Optimize for web playback
        )
        .overwrite_output()
        .run()
    )
    
    print(f"Successfully created {output_file}")


# Examples of building file arrays dynamically:

def build_file_array_by_pattern(directory, patterns):
    """
    Build file array using multiple patterns
    
    Args:
        directory (str): Base directory
        patterns (list): List of glob patterns
        
    Returns:
        list: Combined and sorted file paths
    """
    all_files = []
    for pattern in patterns:
        files = glob.glob(os.path.join(directory, pattern))
        all_files.extend(files)
    
    return sorted(list(set(all_files)))  # Remove duplicates and sort

def build_file_array_by_sequence(directory, prefix, start, end, extension="ts"):
    """
    Build file array for sequentially numbered files
    
    Args:
        directory (str): Base directory
        prefix (str): File prefix (e.g., "video_")
        start (int): Starting number
        end (int): Ending number
        extension (str): File extension
        
    Returns:
        list: List of file paths in sequence
    """
    files = []
    for i in range(start, end + 1):
        filename = f"{prefix}{i:03d}.{extension}"  # Zero-padded numbers
        filepath = os.path.join(directory, filename)
        if os.path.exists(filepath):
            files.append(filepath)
        else:
            print(f"Warning: Expected file not found: {filepath}")
    
    return files

def build_file_array_by_date(directory, pattern="*.ts", reverse=False):
    """
    Build file array sorted by modification date
    
    Args:
        directory (str): Base directory
        pattern (str): Glob pattern
        reverse (bool): If True, newest files first
        
    Returns:
        list: List of file paths sorted by date
    """
    files = glob.glob(os.path.join(directory, pattern))
    # Sort by modification time
    files.sort(key=os.path.getmtime, reverse=reverse)
    return files

# Usage examples for dynamic array building:
"""
# Example 1: Multiple patterns
file_array = build_file_array_by_pattern("/videos", ["part*.ts", "segment*.ts", "chunk*.ts"])

# Example 2: Sequential files
file_array = build_file_array_by_sequence("/videos", "video_", 1, 100)

# Example 3: By date (oldest first)
file_array = build_file_array_by_date("/videos", "*.ts", reverse=False)

# Example 4: Manual array with custom order
file_array = [
    "/videos/intro.ts",
    "/videos/main_content.ts", 
    "/videos/outro.ts"
]

# Use any of these arrays:
combine_ts_files_to_mp4(file_array, "output.mp4")
"""

# Additional utility functions
def get_video_info(file_path):
    """Get information about a video file"""
    try:
        probe = ffmpeg.probe(file_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
        
        return {
            'duration': float(probe['format']['duration']),
            'video_codec': video_info['codec_name'],
            'resolution': f"{video_info['width']}x{video_info['height']}",
            'audio_codec': audio_info['codec_name'],
            'file_size': int(probe['format']['size'])
        }
    except Exception as e:
        print(f"Error getting info for {file_path}: {e}")
        return None

def validate_ts_files(input_source):
    """
    Validate .ts files before processing
    
    Args:
        input_source (str or list): Directory path, file list path, or list of file paths
        
    Returns:
        list: List of valid file paths
    """
    if isinstance(input_source, list):
        ts_files = input_source.copy()
        print(f"Validating {len(ts_files)} files from array...")
    elif isinstance(input_source, str) and input_source.endswith('.txt'):
        ts_files = read_file_list(input_source)
        print(f"Validating {len(ts_files)} files from file list...")
    else:
        ts_files = sorted(glob.glob(os.path.join(input_source, "*.ts")))
        print(f"Validating {len(ts_files)} files from directory...")
    
    valid_files = []
    
    for i, ts_file in enumerate(ts_files):
        try:
            ffmpeg.probe(ts_file)
            valid_files.append(ts_file)
        except Exception as e:
            print(f"Invalid file {ts_file}: {e}")
        
        if (i + 1) % 100 == 0:
            print(f"Validated {i + 1}/{len(ts_files)} files")
    
    print(f"Found {len(valid_files)} valid .ts files out of {len(ts_files)}")
    return valid_files