import aiohttp
import asyncio
import os
import time
import subprocess
import humanize
from tqdm import tqdm
from urllib.parse import urlparse

# Set the download directory (change this easily)
dldir = "downloads"

# Ensure the directory exists
os.makedirs(dldir, exist_ok=True)

# Function to format bytes into human-readable sizes
def format_size(size):
    return humanize.naturalsize(size, binary=True)

# Function to determine file type from MIME type
def get_file_type(mime_type):
    if mime_type.startswith("video/"):
        return "video"
    elif mime_type.startswith("audio/"):
        return "audio"
    elif mime_type.startswith("image/"):
        return "image"
    elif mime_type.startswith("application/") or mime_type.startswith("text/"):
        return "document"
    else:
        return "unknown"

# Function to get file info (checks if M3U8, gets filename, size, and type)
async def get_file_info(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(url, allow_redirects=True) as response:
                if response.status != 200:
                    return {"error": f"URL not accessible, status: {response.status}"}

                content_type = response.headers.get("Content-Type", "")
                
                # Check if it's an M3U8 file
                is_m3u8 = "application/vnd.apple.mpegurl" in content_type or url.endswith(".m3u8")

                # Get file size
                file_size = response.headers.get("Content-Length")
                file_size = int(file_size) if file_size else None

                # Extract filename
                content_disposition = response.headers.get("Content-Disposition", "")
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[-1].strip().strip('"')
                else:
                    filename = os.path.basename(urlparse(url).path)

                # If filename is missing, generate one
                extension = "mp4" if is_m3u8 else "bin"
                if not filename:
                    filename = f"file_{int(time.time())}.{extension}"

                # Determine file type
                file_type = get_file_type(content_type)
                if is_m3u8:
                    file_type = "video"
                return {
                    "url": url,
                    "filename": filename,
                    "file_size": file_size,
                    "is_m3u8": is_m3u8,
                    "file_type": file_type
                }
        except Exception as e:
            return {"error": str(e)}


# Function to download a file with progress tracking
async def download_file(url, filename=None, msg, chunk_size=1024 * 1024):
    file_info = await get_file_info(url)
    if "error" in file_info:
        print(f"Error: {file_info['error']}")
        await msg.edit_text(f"Err getting file data: {file_info['error']}")
        return

    filename = filename or file_info["filename"]
    file_size = file_info["file_size"]
    
    # Ensure filename is saved in the specified directory
    file_path = os.path.join(dldir, filename)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Error: Unable to download file, status {response.status}")
                    await msg.edit_text(f"Error: Unable to download file, status {response.status}")
                    return
                
                with open(file_path, "wb") as f:
                    start_time = time.time()
                    downloaded = 0

                    # If file size is unknown, download normally
                    if not file_size:
                        print(f"Downloading {filename} (Unknown size)...")
                        await msg.edit_text(f"Downloading {filename} (Unknown size)")
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Calculate percentage, speed
                            elapsed_time = time.time() - start_time
                            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                             
                            await print_progress(filename=filename, downloaded=downloaded, total_size=None, speed=speed, eta=None, msg=msg, st=start_time)
                        print(f"\nDownload complete: {file_path}")
                        await msg.edit_text(f"Download complete: {file_path}")
                        return
                    
                    # If file size is known, show progress
                    with tqdm(total=file_size, unit="B", unit_scale=True, desc=filename) as progress:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Calculate percentage, speed, and ETA
                            elapsed_time = time.time() - start_time
                            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                            eta = (file_size - downloaded) / speed if speed > 0 else 0

                            # Print progress
                            progress.update(len(chunk))
                            await print_progress(filename, downloaded, file_size, speed, eta, msg=msg, st=start_time)

        except Exception as e:
            print(f"Download failed: {str(e)}")
            await msg.edit_text(f"Download failed: {str(e)}")
            return

    print(f"\nDownload complete: {file_path}")
    await msg.edit_text(f"Download complete: {file_path}")

# Function to download M3U8 streams using FFmpeg and show progress
async def download_m3u8(url, filename, msg):
    filename = os.path.join(dldir, filename)  # Save in the specified directory
    print(f"Downloading M3U8 stream: {url} -> {filename}")
    await msg.edit_text(f"Downloading M3U8 stream: {url} -> {filename}")
    
    command = [
        "ffmpeg", "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", filename
    ]

    try:
        # Start process and capture real-time logs
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        start_time = time.time()
        downloaded = 0

        for line in process.stdout:
            # Extract progress from FFmpeg logs
            if "time=" in line:
                elapsed_time = time.time() - start_time
                downloaded += 1024 * 1024  # Simulating 1MB per log update

                speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                await print_progress(filename, downloaded, None, speed, elapsed_time, msg=msg, st=start_time)
        
        process.wait()
        
        if process.returncode != 0:
            print(f"Error: FFmpeg failed to download M3U8 stream.")
            await msg.edit_text(f"Error: FFmpeg failed to download M3U8 stream.")
        else:
            print(f"\nM3U8 Download complete: {filename}")
            await msg.edit_text(f"\nM3U8 Download complete: {filename}")

    except Exception as e:
        print(f"Error downloading M3U8: {str(e)}")
        await msg.edit_text(f"Error downloading M3U8: {str(e)}")

#handled m3u8 dl
async def download_m3u8_2(url, filename, msg):
    filename = os.path.join(dldir, filename)  # Save in the specified directory
    print(f"Downloading M3U8 stream: {url} -> {filename}")
    await msg.edit_text(f"Downloading M3U8 stream: {url} -> {filename}")
    
    command = [
        "ffmpeg", "-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", filename
    ]

    try:
        # Use asyncio for non-blocking process management
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        start_time = time.time()
        downloaded = 0

        async for line in process.stdout:
            # Extract progress from FFmpeg logs
            if "time=" in line:
                elapsed_time = time.time() - start_time
                downloaded += 1024 * 1024  # Simulating 1MB per log update

                speed = downloaded / elapsed_time if elapsed_time > 0 else 0
                await print_progress(filename, downloaded, None, speed, elapsed_time, msg=msg, st=start_time)
        
        # Wait for the process to finish
        await process.wait()

        if process.returncode != 0:
            print(f"Error: FFmpeg failed to download M3U8 stream.")
            await msg.edit_text(f"Error: FFmpeg failed to download M3U8 stream.")
        else:
            print(f"\nM3U8 Download complete: {filename}")
            await msg.edit_text(f"\nM3U8 Download complete: {filename}")

    except Exception as e:
        print(f"Error downloading M3U8: {str(e)}")
        await msg.edit_text(f"Error downloading M3U8: {str(e)}")


last_msg=""
last_t=0
# Function to print progress updates
async def print_progress(filename, downloaded, total_size, speed, eta, msg=None, st):
    eta_str = f"{int(eta)}s" if eta else "Unknown"
    percent_done = f"{(downloaded / total_size) * 100:.2f}%" if total_size else "Unknown"
    speed_str = format_size(speed) + "/s" if speed else "Unknown"
    size_done = format_size(downloaded)
    total_size_str = format_size(total_size) if total_size else "Unknown"

    print(f"\r{filename}: {size_done}/{total_size_str} ({percent_done}) at {speed_str}, ETA: {eta_str}", end="", flush=True)
    etime = time.time() - start_time
    if msg:
        if last_t == 0 or time.time() - last_t >= 10:
            new_msg = f"**Downloading...**\n\nName : {filename}\nDone : {size_done}/{total_size_str}\nP : {percent_done}\nSpeed : {speed_str}\nETA: {eta_str}"
            if last_msg != new_msg:
                await msg.edit_text(new_msg)
                last_msg = new_msg
                last_t = time.time()

# Function to start the download (supports custom filename)
async def dl(url, msg, custom_filename=None):
    file_info = await get_file_info(url)

    if "error" in file_info:
        print(f"Error: {file_info['error']}")
        await msg.edit_text(f"Err getting file data: {file_info['error']}")
        return {"error": file_info["error"]}

    filename = custom_filename if custom_filename else file_info["filename"]
    file_path = os.path.join(dldir, filename)

    try:
        if file_info["is_m3u8"]:
            # Call download_m3u8 function
            await download_m3u8(url, filename, msg=msg)
        else:
            # Call download_file function
            await download_file(url, filename, msg=msg)

        return {"filename": filename, "file_path": file_path}
    
    except Exception as e:
        print(f"Error during download: {str(e)}")
        await msg.edit_text(f"Error: {str(e)}")
        return {"error": str(e)}
