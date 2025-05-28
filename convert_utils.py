"""
Optimized AAC to MP3 Converter Module
------------------------------------
This module provides memory-efficient functions to convert AAC files to MP3 format.
Optimized for processing thousands of files with minimal memory usage.

Requirements:
- pydub (pip install pydub)
- ffmpeg (must be installed on your system and available in PATH)
"""

import os
import gc
import time
import glob
import ffmpeg
import shutil
import asyncio
import aiohttp
import aiofiles
import tempfile
from pathlib import Path
from pydub import AudioSegment
from colorama import Fore
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from typing import List, Optional

# Configuration constants
CHUNK_SIZE = 100  # Process files in chunks to manage memory
TEMP_SEGMENT_DURATION = 300000  # 5 minutes in milliseconds
MAX_WORKERS = min(4, mp.cpu_count())  # Limit concurrent processes

def convert_aac_to_mp3_streaming(input_directory=None, output_file=None, pattern="*.aac", 
                                file_list=None, verbose=True, chunk_size=CHUNK_SIZE,
                                use_temp_files=True):
    """
    Convert multiple AAC files to a single MP3 file using streaming approach.
    Optimized for memory efficiency when processing thousands of files.
    
    Args:
        input_directory (str, optional): Directory containing AAC files
        output_file (str): Path to save the final MP3 file
        pattern (str): Glob pattern to match AAC files (default: "*.aac")
        file_list (list, optional): Explicit list of AAC file paths
        verbose (bool): Whether to print progress messages
        chunk_size (int): Number of files to process in each chunk
        use_temp_files (bool): Use temporary files for intermediate processing
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    # Get list of AAC files
    aac_files = _get_file_list(input_directory, pattern, file_list, verbose)
    if not aac_files:
        return False
    
    if verbose:
        print(f"{Fore.MAGENTA}Found {len(aac_files)} AAC files to convert{Fore.WHITE}")
    
    try:
        if use_temp_files and len(aac_files) > chunk_size:
            return _process_with_temp_files(aac_files, output_file, chunk_size, verbose)
        else:
            return _process_streaming(aac_files, output_file, verbose)
    
    except Exception as e:
        if verbose:
            print(f"{Fore.RED}Error during conversion: {Fore.YELLOW}{e}{Fore.WHITE}")
        return False

def convert_aac_to_mp3_parallel(input_directory=None, output_file=None, pattern="*.aac",
                               file_list=None, verbose=True, max_workers=MAX_WORKERS):
    """
    Convert multiple AAC files to MP3 using parallel processing.
    Best for systems with multiple CPU cores and sufficient RAM.
    
    Args:
        input_directory (str, optional): Directory containing AAC files
        output_file (str): Path to save the final MP3 file
        pattern (str): Glob pattern to match AAC files
        file_list (list, optional): Explicit list of AAC file paths
        verbose (bool): Whether to print progress messages
        max_workers (int): Maximum number of parallel workers
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    aac_files = _get_file_list(input_directory, pattern, file_list, verbose)
    if not aac_files:
        return False
    
    if verbose:
        print(f"{Fore.MAGENTA}Found {len(aac_files)} AAC files for parallel conversion{Fore.WHITE}")
    
    try:
        # Split files into chunks for parallel processing
        chunk_size = max(1, len(aac_files) // max_workers)
        file_chunks = [aac_files[i:i + chunk_size] for i in range(0, len(aac_files), chunk_size)]
        
        temp_files = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Process chunks in parallel
            futures = []
            for i, chunk in enumerate(file_chunks):
                temp_output = f"{output_file}.temp_{i}.mp3"
                temp_files.append(temp_output)
                future = executor.submit(_process_chunk_to_file, chunk, temp_output, verbose and i == 0)
                futures.append(future)
            
            # Wait for all chunks to complete
            for i, future in enumerate(futures):
                if verbose:
                    print(f"{Fore.CYAN}Completed chunk {i+1}/{len(futures)}{Fore.WHITE}")
                future.result()
        
        # Combine all temporary files
        if verbose:
            print(f"{Fore.MAGENTA}Combining {len(temp_files)} temporary files...{Fore.WHITE}")
        
        _combine_temp_files(temp_files, output_file, verbose)
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass
        
        if verbose:
            print(f"{Fore.MAGENTA}Parallel conversion complete!{Fore.WHITE}")
        return True
    
    except Exception as e:
        if verbose:
            print(f"{Fore.RED}Error during parallel conversion: {Fore.YELLOW}{e}{Fore.WHITE}")
        return False

def _get_file_list(input_directory, pattern, file_list, verbose):
    """Get and validate the list of files to process."""
    if file_list:
        return [f for f in file_list if os.path.exists(f)]
    elif input_directory:
        return sorted(glob(os.path.join(input_directory, pattern)))
    else:
        if verbose:
            print(f"{Fore.RED}Error: {Fore.YELLOW}Either input_directory or file_list must be provided{Fore.WHITE}")
        return []

def _process_streaming(aac_files, output_file, verbose):
    """Process files using streaming approach - loads one file at a time."""
    combined_audio = None
    
    for i, aac_file in enumerate(aac_files):
        if verbose:
            print(f"\033[H\033[J{Fore.MAGENTA}Processing: {Fore.YELLOW}{i+1}/{len(aac_files)} - {os.path.basename(aac_file)}{Fore.WHITE}")
        
        # Load current file
        current_audio = AudioSegment.from_file(aac_file, format="aac")
        
        if combined_audio is None:
            combined_audio = current_audio
        else:
            combined_audio += current_audio
        
        # Explicit cleanup
        del current_audio
        gc.collect()
    
    # Export final result
    if verbose:
        print(f"{Fore.MAGENTA}Exporting to MP3: {Fore.CYAN}{output_file}{Fore.WHITE}")
    
    combined_audio.export(output_file, format="mp3")
    del combined_audio
    gc.collect()
    
    return True

def _process_with_temp_files(aac_files, output_file, chunk_size, verbose):
    """Process files in chunks using temporary files to manage memory."""
    temp_dir = tempfile.mkdtemp(prefix="aac_convert_")
    temp_files = []
    
    try:
        # Process files in chunks
        for chunk_idx in range(0, len(aac_files), chunk_size):
            chunk = aac_files[chunk_idx:chunk_idx + chunk_size]
            temp_output = os.path.join(temp_dir, f"chunk_{chunk_idx//chunk_size}.mp3")
            temp_files.append(temp_output)
            
            if verbose:
                print(f"{Fore.CYAN}Processing chunk {chunk_idx//chunk_size + 1} ({len(chunk)} files)...{Fore.WHITE}")
            
            # Process this chunk
            combined_chunk = None
            for i, aac_file in enumerate(chunk):
                if verbose:
                    print(f"\033[H\033[J{Fore.MAGENTA}Chunk {chunk_idx//chunk_size + 1}: {Fore.YELLOW}{i+1}/{len(chunk)} - {os.path.basename(aac_file)}{Fore.WHITE}")
                
                current_audio = AudioSegment.from_file(aac_file, format="aac")
                
                if combined_chunk is None:
                    combined_chunk = current_audio
                else:
                    combined_chunk += current_audio
                
                del current_audio
                gc.collect()
            
            # Save chunk to temporary file
            combined_chunk.export(temp_output, format="mp3")
            del combined_chunk
            gc.collect()
        
        # Combine all temporary files
        if verbose:
            print(f"{Fore.MAGENTA}Combining {len(temp_files)} chunks...{Fore.WHITE}")
        
        _combine_temp_files(temp_files, output_file, verbose)
        
        return True
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

def _process_chunk_to_file(file_chunk, output_file, verbose):
    """Process a chunk of files and save to output file. Used for parallel processing."""
    combined_audio = None
    
    for i, aac_file in enumerate(file_chunk):
        if verbose:
            print(f"Processing {i+1}/{len(file_chunk)}: {os.path.basename(aac_file)}")
        
        current_audio = AudioSegment.from_file(aac_file, format="aac")
        
        if combined_audio is None:
            combined_audio = current_audio
        else:
            combined_audio += current_audio
        
        del current_audio
        gc.collect()
    
    combined_audio.export(output_file, format="mp3")
    del combined_audio
    gc.collect()

def _combine_temp_files(temp_files, output_file, verbose):
    """Combine multiple temporary MP3 files into a single output file."""
    combined_audio = None
    
    for i, temp_file in enumerate(temp_files):
        if verbose:
            print(f"{Fore.CYAN}Combining file {i+1}/{len(temp_files)}{Fore.WHITE}")
        
        current_audio = AudioSegment.from_file(temp_file, format="mp3")
        
        if combined_audio is None:
            combined_audio = current_audio
        else:
            combined_audio += current_audio
        
        del current_audio
        gc.collect()
    
    combined_audio.export(output_file, format="mp3")
    del combined_audio
    gc.collect()

# Convenience function that automatically chooses the best method
def convert_aac_to_mp3_auto(input_directory=None, output_file=None, pattern="*.aac",
                           file_list=None, verbose=True):
    """
    Automatically choose the best conversion method based on file count and system resources.
    
    Args:
        input_directory (str, optional): Directory containing AAC files
        output_file (str): Path to save the final MP3 file
        pattern (str): Glob pattern to match AAC files
        file_list (list, optional): Explicit list of AAC file paths
        verbose (bool): Whether to print progress messages
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    aac_files = _get_file_list(input_directory, pattern, file_list, verbose)
    if not aac_files:
        return False
    
    file_count = len(aac_files)
    
    if verbose:
        print(f"{Fore.MAGENTA}Auto-selecting conversion method for {file_count} files...{Fore.WHITE}")
    
    # Choose method based on file count and system capabilities
    if file_count < 50:
        if verbose:
            print(f"{Fore.CYAN}Using streaming method for small file count{Fore.WHITE}")
        return convert_aac_to_mp3_streaming(file_list=aac_files, output_file=output_file, 
                                          verbose=verbose, use_temp_files=False)
    elif file_count < 500 and mp.cpu_count() > 2:
        if verbose:
            print(f"{Fore.CYAN}Using parallel method for medium file count{Fore.WHITE}")
        return convert_aac_to_mp3_parallel(file_list=aac_files, output_file=output_file, verbose=verbose)
    else:
        if verbose:
            print(f"{Fore.CYAN}Using chunked temp file method for large file count{Fore.WHITE}")
        return convert_aac_to_mp3_streaming(file_list=aac_files, output_file=output_file, 
                                          verbose=verbose, use_temp_files=True, chunk_size=CHUNK_SIZE)

# Backward compatibility - keep original function name
def convert_aac_to_mp3(input_directory=None, output_file=None, pattern="*.aac", 
                      file_list=None, verbose=True):
    """
    Original function name maintained for backward compatibility.
    Now uses the optimized auto-selection method.
    """
    return convert_aac_to_mp3_auto(input_directory, output_file, pattern, file_list, verbose)



async def download_single_file(session: aiohttp.ClientSession, media_url: str, file: str, output_path: str, semaphore: asyncio.Semaphore) -> tuple[str, bool]:
    """Download a single file with semaphore for concurrency control"""
    async with semaphore:
        file_name = os.path.basename(file)
        file_path = os.path.join(output_path, file_name)
        
        # Skip if file already exists
        if os.path.exists(file_path):
            return file, True
            
        try:
            url = f"{media_url}{file}"
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):  # Larger chunks
                            await f.write(chunk)
                    return file, True
                else:
                    print(f"{Fore.RED}Failed to download {file}: HTTP {response.status}{Fore.WHITE}")
                    return file, False
        except Exception as e:
            print(f"{Fore.RED}Failed to download {file}: {e}{Fore.WHITE}")
            return file, False

async def async_download_media(media_url: Optional[str] = None, files: List[str] = [], 
                             output_path: Optional[str] = None, verbose: bool = True,
                             max_concurrent: int = 10) -> Optional[bool]:
    """
    Optimized async file downloader with concurrent downloads
    
    Args:
        media_url: Base URL for files
        files: List of file paths to download
        output_path: Directory to save files
        verbose: Whether to show progress
        max_concurrent: Maximum number of concurrent downloads
    """
    if not media_url and not files:
        print(f"{Fore.RED}No {Fore.YELLOW}media_url{Fore.RED} or {Fore.YELLOW}files{Fore.RED} provided...{Fore.WHITE}")
        return None
    
    # Use current directory if no output path specified
    if output_path is None:
        output_path = os.getcwd()
    
    if not os.path.exists(output_path):
        print(f"{Fore.RED}Output path {output_path} does not exist{Fore.WHITE}")
        return None

    if not files:
        return True

    print(f"{Fore.MAGENTA}Starting download of {len(files)} files with {max_concurrent} concurrent connections...{Fore.WHITE}")
    
    # Create semaphore to limit concurrent downloads
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Configure session with optimized settings
    timeout = aiohttp.ClientTimeout(total=300, connect=30)  # 5 min total, 30s connect
    connector = aiohttp.TCPConnector(
        limit=50,  # Total connection pool size
        limit_per_host=max_concurrent,  # Connections per host
        keepalive_timeout=30,
        enable_cleanup_closed=True
    )
    
    start_time = time.time()
    completed = 0
    failed = 0
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # Create tasks for all downloads
        tasks = [
            download_single_file(session, media_url, file, output_path, semaphore)
            for file in files
        ]
        
        # Process downloads with progress updates
        if verbose:
            for coro in asyncio.as_completed(tasks):
                file, success = await coro
                completed += 1
                
                if success:
                    status = f"{Fore.GREEN}✓{Fore.WHITE}"
                else:
                    status = f"{Fore.RED}✗{Fore.WHITE}"
                    failed += 1
                
                # Clear screen and show progress
                print(f"\033[H\033[J")
                print(f"{Fore.MAGENTA}Downloading Files: {Fore.YELLOW}{completed}/{len(files)}{Fore.WHITE}")
                
                # Progress bar
                progress = completed / len(files)
                bar_length = 40
                filled_length = int(bar_length * progress)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                percentage = progress * 100
                
                print(f"{Fore.BLUE}[{bar}] {Fore.YELLOW}{percentage:.1f}%{Fore.WHITE}")
                print(f"{Fore.GREEN}Success: {completed - failed} {Fore.RED}Failed: {failed}{Fore.WHITE}")
                
                if completed < len(files):
                    print(f"{Fore.CYAN}Last: {status} {os.path.basename(file)}{Fore.WHITE}")
        else:
            # Just wait for all to complete without progress updates
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, tuple) and result[1]:
                    completed += 1
                else:
                    failed += 1
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{Fore.GREEN}Download completed!{Fore.WHITE}")
    print(f"{Fore.CYAN}Total: {len(files)} | Success: {completed - failed} | Failed: {failed}{Fore.WHITE}")
    print(f"{Fore.YELLOW}Time: {elapsed_time:.2f}s | Avg: {elapsed_time/len(files):.2f}s per file{Fore.WHITE}")
    
    return failed == 0





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


