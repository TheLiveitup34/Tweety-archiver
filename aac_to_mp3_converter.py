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
import tempfile
import shutil
from pathlib import Path
from glob import glob
from pydub import AudioSegment
from colorama import Fore
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

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