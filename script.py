#!/usr/bin/env python3

"""
===================================================================
File Name:      script.py
Author:         Armoghan-ul-Mohmin
Date:           2025-03-10
Description:    
    This script extracts frames from a given video file and saves 
    them as individual image files in a specified directory.
    
    It supports multithreading for faster processing and displays 
    video metadata in a table format using Rich. The script also 
    provides a progress bar to track frame extraction.

Usage:         
    python3 script.py <video> <dir> [--threads N]

    Arguments:
        <video>      Path to the video file.
        <dir>        Directory where extracted frames will be saved.
    
    Optional:
        --threads N  Number of threads to use (default: 4).

Dependencies:
    - OpenCV (cv2)
    - Rich (for terminal visualization)
    - argparse (for command-line parsing)
    - concurrent.futures (for multithreading)
    - pathlib (for cross-platform path handling)

Example:
    python3 script.py sample.mp4 frames --threads 8
===================================================================
"""

import cv2
import os
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

def save_frame(frame, frame_count, dir):
    """
    Saves a single frame as an image file.
    
    Args:
        frame (numpy.ndarray): The image frame data.
        frame_count (int): The frame index number.
        dir (str): The directory where frames will be saved.
    """
    frame_path = os.path.join(dir, f"frame_{frame_count:04d}.jpg")
    cv2.imwrite(frame_path, frame)

def extract_frames(video, dir, threads=4):
    """
    Extracts frames from a video file and saves them as images.
    
    Args:
        video (str): Path to the video file.
        dir (str): Path to the output directory.
        threads (int): Number of threads for frame extraction.
    """
    try:
        # Validate video file existence
        if not Path(video).is_file():
            console.print(f"[bold red]Error: Video file '{video}' not found![/bold red]")
            return

        # Create the output directory if it doesn't exist
        Path(dir).mkdir(parents=True, exist_ok=True)

        # Open the video file
        cap = cv2.VideoCapture(video)
        if not cap.isOpened():
            console.print("[bold red]Error: Failed to open video file![/bold red]")
            return

        # Retrieve video metadata
        fps = cap.get(cv2.CAP_PROP_FPS) or 30  # Default to 30 FPS if unavailable
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else "Unknown"

        # Get codec information
        codec = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec_str = "".join([chr((codec >> 8 * i) & 0xFF) for i in range(4)]) if codec else "Unknown"

        # Prepare metadata for display
        metadata = {
            "FPS": fps,
            "Total Frames": total_frames,
            "Duration": f"{duration:.2f} sec" if isinstance(duration, float) else "Unknown",
            "Resolution": f"{width}x{height}",
            "Codec": codec_str,
        }

        # Display video metadata
        table = Table(title="Video Information", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="dim", width=20)
        table.add_column("Value", style="bold yellow")
        for key, value in metadata.items():
            table.add_row(key, str(value))
        console.print(table)

        # Extract frames
        frame_count = 0
        futures = []

        with Progress() as progress:
            task = progress.add_task("[cyan]Extracting frames...", total=total_frames)
            with ThreadPoolExecutor(max_workers=threads) as executor:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break  # Stop when the video ends
                    
                    # Submit frame saving task
                    futures.append(executor.submit(save_frame, frame, frame_count, dir))
                    frame_count += 1
                    progress.update(task, advance=1)

                # Wait for all threads to finish
                for future in as_completed(futures):
                    future.result()

        # Release the video file
        cap.release()

        console.print(f"\n[bold green]Success! Extracted {frame_count} frames from '{video}'.[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

def main():
    """
    Main function to parse command-line arguments and start frame extraction.
    """
    parser = argparse.ArgumentParser(description="Extract frames from a video file")
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument("dir", help="Directory where extracted frames will be saved")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads (default: 4)")
    args = parser.parse_args()

    # Start frame extraction
    extract_frames(args.video, args.dir, args.threads)

if __name__ == "__main__":
    main()