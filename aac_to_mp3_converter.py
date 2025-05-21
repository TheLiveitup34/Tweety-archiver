"""
AAC to MP3 Converter Module
--------------------------
This module provides functions to convert AAC files to MP3 format.
Requirements:
- pydub (pip install pydub)
- ffmpeg (must be installed on your system and available in PATH)
"""

import os
from glob import glob
from pydub import AudioSegment
from colorama import Fore

def convert_aac_to_mp3(input_directory=None, output_file=None, pattern="*.aac", file_list=None, verbose=True):
    """
    Convert multiple AAC files to a single MP3 file.
    
    Args:
        input_directory (str, optional): Directory containing AAC files
        output_file (str): Path to save the final MP3 file
        pattern (str): Glob pattern to match AAC files (default: "*.aac")
        file_list (list, optional): Explicit list of AAC file paths to use instead of scanning a directory
        verbose (bool): Whether to print progress messages
    
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    # Get list of AAC files
    aac_files = []
    
    if file_list:
        # Use provided list of files
        aac_files = file_list
    elif input_directory:
        # Scan directory for files matching pattern
        aac_files = sorted(glob(os.path.join(input_directory, pattern)))
    else:
        if verbose:
            print(f"{Fore.RED}Error: {Fore.YELLOW}Either input_directory or file_list must be provided{Fore.WHITE}")
        return False
    
    if not aac_files:
        if verbose:
            print(f"{Fore.RED}No AAC files found to convert{Fore.WHITE}")
        return False
    
    if verbose:
        print(f"{Fore.MAGENTA}Found {len(aac_files)} AAC files to convert{Fore.WHITE}")
    
    # Initialize combined audio with the first file
    if verbose:
        print(f"\033[H\033[J")
        print(f"{Fore.MAGENTA}Converting Files to a MP3 File: {Fore.YELLOW}1/{len(aac_files)}{Fore.WHITE}")
        print(f"{Fore.MAGENTA}Processing: {Fore.YELLOW}{os.path.basename(aac_files[0])}{Fore.WHITE}")
    
    try:
        combined_audio = AudioSegment.from_file(aac_files[0], format="aac")
        
        # Append each additional file
        file_number = 2
        for aac_file in aac_files[1:]:
            if verbose:
                print(f"\033[H\033[J")
                print(f"{Fore.MAGENTA}Converting Files to a MP3 File: {Fore.YELLOW}{file_number}/{len(aac_files)}{Fore.WHITE}")
                file_number += 1
                print(f"{Fore.MAGENTA}Processing: {Fore.YELLOW}{os.path.basename(aac_file)}{Fore.WHITE}")
            audio = AudioSegment.from_file(aac_file, format="aac")
            combined_audio += audio
            del audio
        
        # Export as MP3
        if verbose:
            print(f"{Fore.MAGENTA}Exporting to MP3: {Fore.CYAN}{output_file}{Fore.WHITE}")
        combined_audio.export(output_file, format="mp3")
        # clear varibales to free memory
        del combined_audio
        del aac_files
        del aac_file
        del input_directory
        del pattern
        del file_list

        if verbose:
            print(f"{Fore.MAGENTA}Conversion complete!{Fore.WHITE}")
            del verbose
        return True
    
    except Exception as e:
        if verbose:
            print(f"{Fore.RED}Error during conversion: {Fore.YELLOW}{e}{Fore.WHITE}")
        return False

