import os
import subprocess
import requests
import base64
import sys
import time
import re
import ffmpeg
from config import Config
from pymediainfo import MediaInfo
from moviepy.editor import VideoFileClip
last_msg = ""
last_upt = 0


def get_media_info(file_path, thumb_path=None):
    try:
        probe = ffmpeg.probe(file_path)
        duration = int(float(probe["format"]["duration"])) if "duration" in probe["format"] else 0
        if not thumb_path:
            thumb_path = f"{file_path}.jpg"
            (
                ffmpeg.input(file_path, ss=1)
                .output(thumb_path, vframes=1)
                .run(capture_stdout=True, capture_stderr=True)
            )
        return duration, thumb_path
    except Exception as e:
        print(f"FFmpeg Error: {e}")
        return None, None


def get_video_duration(input_video_path):
    """Get the total duration of the video in seconds using MoviePy."""
    try:
        video = VideoFileClip(input_video_path)
        duration = video.duration  # Duration in seconds
        print(f"Video duration: {duration} seconds")
        return duration
    except Exception as e:
        print(f"Error: {e}")
        return None

async def u_msg(msg, start_t, txt):
  global last_msg, last_upt
  if txt != last_msg:
    if (time.time() - last_upt) >= 10:
      ms = await msg.edit_text(txt)
      last_msg = txt
      last_upt = time.time()
      return ms


def gget_video_duration(video_path):
    media_info = MediaInfo.parse(video_path)
    for track in media_info.tracks:
        if track.track_type == "Video":
            return track.duration / 1000  # Convert ms to seconds
    return None


def gghet_video_duration(input_video_path):
    """Get the total duration of the video in seconds using FFmpeg."""
    cmd = [
        'ffmpeg', '-i', input_video_path,
        '-hide_banner', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'format=duration', '-of', 'csv=p=0'
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        dr=float(result.stdout.strip())
        print(f"durationnn: {dr}")
        return dr
    except ValueError:
        return None


async def convert_to_hls(input_video_path, output_dir, msg):
    """Convert video to HLS and show progress in percentage."""
    global last_msg, last_upt
    await msg.edit_text("Starting Coverting...!")
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get video duration
    total_duration, thumb = get_media_info(input_video_path)
    if thumb:
        await msg.edit_text("uploding thumb")
        await upload_to_github(thumb, output_dir)
    if total_duration is None:
        print("Error: Unable to determine video duration.")
        await msg.edit_text("Unable to get video duration.")
        return None, None

    start_t = time.time()
    # Run the FFmpeg command to convert video to HLS
    output_m3u8 = os.path.join(output_dir, 'output.m3u8')
    cmd = [
        'ffmpeg', '-i', input_video_path,
        '-preset', 'ultrafast', '-g', '48', '-sc_threshold', '0',
        '-hls_time', '10', '-hls_list_size', '0',
        '-hls_segment_filename', os.path.join(output_dir, 'segment_%03d.ts'),
        output_m3u8
    ]
    await msg.edit_text()
    # Run FFmpeg command and capture its output in real-time
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Parse FFmpeg stderr for progress
    while process.poll() is None:
        output = process.stderr.readline()
        print(output, end="")  # Optional: Print raw FFmpeg output for debugging
        
        match = re.search(r"time=(\d+):(\d+):([\d.]+)", output)
        if match:
            hours, minutes, seconds = map(float, match.groups())
            elapsed_seconds = hours * 3600 + minutes * 60 + seconds
            percentage = (elapsed_seconds / total_duration) * 100
            #pmsg = f"FFmpeg Progress: {percentage:.2f}% complete"
            pmsg =f"Ffmpeg : e time:{elapsed_seconds}"
            print(pmsg, end="")
            await u_msg(msg, start_t, pmsg)
    
    print("\nFFmpeg Conversion Complete.")
    await msg.edit_text("Converted!..")
    return output_m3u8, output_dir


# Function to convert video to HLS and show FFmpeg progress
async def cconvert_to_hls(input_video_path, output_dir):
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Run the FFmpeg command to convert video to HLS
    output_m3u8 = os.path.join(output_dir, 'output.m3u8')
    cmd = [
        'ffmpeg', '-i', input_video_path,
        '-preset', 'ultrafast', '-g', '48', '-sc_threshold', '0',
        '-hls_time', '10', '-hls_list_size', '0',
        '-hls_segment_filename', os.path.join(output_dir, 'segment_%03d.ts'),
        output_m3u8
    ]
    
    # Run FFmpeg command and capture its output in real time
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Parse FFmpeg stderr for progress
    while process.poll() is None:
        output = process.stderr.readline()
        print(output)
        if "time=" in output:
            # Extract time value from the output
            time_info = output.split("time=")[-1].split(" ")[0]
            if not 'N/A' in time_info:
              time_parts = time_info.split(":")
              elapsed_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + float(time_parts[2])
              print(f"FFmpeg Progress: {elapsed_seconds:.2f} seconds", end="\r")
        #time.sleep(1)
    
    print("\nFFmpeg Conversion Complete.")
    return output_m3u8, output_dir

# Function to upload a file to GitHub with progress tracking
def upload_to_github(file_path, upload_dir):
    url = f"https://api.github.com/repos/{Config.GIT_UN}/{Config.GIT_REPO}/contents/{upload_dir}/{os.path.basename(file_path)}"
    
    with open(file_path, "rb") as file:
      content = file.read()
    
    content_b64 = base64.b64encode(content).decode("utf-8")
    payload = {
        "message": f"Upload {os.path.basename(file_path)}",
        "branch": Config.GIT_BRANCH,
        "content": content_b64
    }
    
    headers = {
        "accept":"application/vnd.github+json",
        "Authorization": f"token {Config.GIT_TK}"
    }
    
    # Track progress by uploading in chunks
    total_size = len(content)
    uploaded_size = 0
    chunk_size = 1024 * 100  # 100 KB chunk size for upload tracking

    #while uploaded_size < total_size:
    chunk = content[uploaded_size:uploaded_size + chunk_size]
    uploaded_size += len(chunk)
        
    response = requests.put(url, json=payload, headers=headers)
        
    if response.status_code == 201:
        print(f"Uploading {os.path.basename(file_path)}: {min(uploaded_size / total_size * 100, 100):.2f}% complete", end="\r")
    else:
        rr=f"Failed to upload {file_path}{response.status_code}: {response.text}"
        print(rr)
        return {"error":f"Filed to upload!: {file_path}_code: {response.status_code}"}
    #time.sleep(1)
    
    rr =f"\nSuccessfully uploaded: {file_path}"
    print(rr)
    return rr

# Function to delete the temporary directory and its contents
def delete_dir(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(directory)
    print(f"Deleted temporary directory: {directory}")

# Main function
async def main(video_path, msg):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_dir = f"{video_name}"
    await msg.reply(f"videopath: {video_path} \n vi name: {video_name}")
    # Convert video to HLS
    m3u8_file, ts_dir = await convert_to_hls(video_path, video_dir, msg)
    
    # Upload m3u8 file
    await upload_to_github(m3u8_file, video_name)
    
    seg_count = len(os.listdir(ts_dir))
    done_segs = 0
    # Upload each .ts segment
    for ts_file in os.listdir(ts_dir):
        if ts_file.endswith(".ts"):
            ts_file_path = os.path.join(ts_dir, ts_file)
            xx = upload_to_github(ts_file_path, video_name)
            if "error" in xx:
                await msg.edit_text(xx["error"])
                break
            done_segs+=1
            pr = (len(done_segs) / seg_count) * 100
            p_msg = f"Uploading..!\n\n{len(done_segs)} of {seg_count} streamfiles...\n\nP: {round(pr,2)}%"
            await u_msg(msg, start_t, p_msg)
            #time.sleep(0.5)
            
    # Delete the temporary files and directories
    delete_dir(video_dir)

async def to_git(file_path, msg):
    #video_path = input("Enter the path to your video: ")
    repo = f"{Config.GIT_UN}/{Config.GIT_REPO}"  # Replace with your repository name
    branch = Config.GIT_BRANCH  # GitHub branch to upload to (default is "main")
    github_token = Config.GIT_TK# look like "ghp_pxbu30smvw9nOdLQ1qbeqcx63yg0GOLgD"  # Replace with your GitHub token

    await main(file_path, msg)
    return 
