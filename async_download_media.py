import asyncio
import aiohttp
import aiofiles
import os
import time
from colorama import Fore
from typing import List, Optional

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



