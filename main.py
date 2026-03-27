#!/usr/bin/env python3
"""
Beat Saber Playlist Generator - ALWAYS extracts to songs/ inside source dir
"""

import argparse
import os
import json
import base64
from zipfile import ZipFile, BadZipFile
import requests
from pathlib import Path
from hashlib import sha1


def get_map_hash_local(map_folder_path):
    """Calculate Beat Saber song hash, maybe don't work with some maps"""
    data = b''

    # 1. Info.dat or info.dat
    info_path = None
    for info_name in ['Info.dat', 'info.dat']:
        test_path = os.path.join(map_folder_path, info_name)
        if os.path.exists(test_path):
            info_path = test_path
            break

    if not info_path:
        return None

    with open(info_path, 'rb') as f:
        data += f.read()

    # 2. difficultyBeatmapSets or fallback
    try:
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        beatmap_sets = info.get('_difficultyBeatmapSets', [])
        if beatmap_sets:
            exclude_types = {'Lightshow', 'AudioData'}
            for beatmap_set in beatmap_sets:
                for beatmap in beatmap_set.get('_difficultyBeatmaps', []):
                    beatmap_file = beatmap.get('_beatmapFilename')
                    full_path = os.path.join(map_folder_path, beatmap_file)
                    if os.path.exists(full_path):
                        with open(full_path, 'rb') as f:
                            data += f.read()
            return sha1(data).hexdigest().upper()
    except:
        pass

    # 3. Fallback by difficulty order
    exclude_files = {'info.dat', 'lightshow.dat', 'audiodata.dat'}
    difficulty_order = ['Normal', 'Hard', 'Expert', 'ExpertPlus', 'OneSaber', 'LivingAGhost']

    all_dat_files = []
    for root, dirs, files in os.walk(map_folder_path):
        for file in files:
            if file.lower().endswith('.dat') and file.lower() not in exclude_files:
                full_path = os.path.join(root, file)
                all_dat_files.append(full_path)

    def diff_key(path):
        filename = os.path.basename(path).lower()
        for i, diff in enumerate(difficulty_order):
            if diff.lower() in filename:
                return i
        return 999

    all_dat_files.sort(key=diff_key)
    for dat_path in all_dat_files:
        with open(dat_path, 'rb') as f:
            data += f.read()

    return sha1(data).hexdigest().upper()


def get_map_hash_online(song_id):
    """Beatsaver API hash lookup"""
    try:
        r = requests.get(f"https://api.beatsaver.com/maps/id/{song_id}", timeout=5)
        r.raise_for_status()
        return r.json()["versions"][0]["hash"].upper()
    except:
        return None


def image_to_base64(image_path):
    """Image to base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def interactive_mode():
    """Interactive mode - ask questions"""
    print("🎵 Beat Saber Playlist Generator (Interactive)")
    print("=" * 50)

    playlist_name = input("Playlist name: ").strip()
    if not playlist_name:
        print("❌ Name required")
        return

    playlist_author = input("Author (Enter=Generator): ").strip() or "Generator"

    songs_dir = input("Songs ZIP directory: ").strip()
    if not songs_dir or not os.path.isdir(songs_dir):
        print("❌ Invalid songs directory")
        return

    image_path = input("Cover image (optional): ").strip()
    use_online = input("Use online API? (y/n, default=y) (local maybe work incorrect): ").strip().lower() in ['y', 'yes', '']

    output_dir = ""
    if not output_dir:
        output_dir = os.path.join(songs_dir, "songs")

    verbose = True

    dry_run = False

    return {
        'songs_dir': songs_dir,
        'name': playlist_name,
        'author': playlist_author,
        'online': use_online,
        'local': not use_online,
        'image': image_path if image_path else None,
        'output_dir': output_dir,
        'verbose': verbose,
        'dry_run': dry_run
    }


def main():
    import sys

    parser = argparse.ArgumentParser(description="Beat Saber playlist generator")
    parser.add_argument('-s', '--songs_dir', required=True, help="ZIP songs directory")
    parser.add_argument('-n', '--name', required=True, help="Playlist name")
    parser.add_argument('-a', '--author', default="Generator", help="Author")
    parser.add_argument('--online', action='store_true', default=True, help="Try API first")
    parser.add_argument('--local', action='store_true', help="Force local hash")
    parser.add_argument('-i', '--image', help="Cover image")
    parser.add_argument('-o', '--output_dir', help="Custom output dir")
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--dry-run', action='store_true')

    # 🆕 ПРОВЕРКА: интерактив ИЛИ CLI
    if len(sys.argv) == 1:  # Только python script.py
        print("🖱️  Interactive mode...")
        args_dict = interactive_mode()
        if not args_dict:
            return
        args = argparse.Namespace(**args_dict)
    else:
        args = parser.parse_args()  # Нормальный CLI парсинг

    # Остальной твой код БЕЗ ИЗМЕНЕНИЙ ↓
    songs_dir = Path(args.songs_dir).expanduser().resolve()
    if not songs_dir.is_dir():
        print(f"❌ {songs_dir} not found")
        return

    default_out_dir = songs_dir / "songs"
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_out_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"📁 Input:  {songs_dir}")
        print(f"💾 Output: {output_dir}")

    playlist = {
        "playlistTitle": args.name,
        "playlistAuthor": args.author,
        "songs": []
    }

    if args.image:
        playlist["image"] = image_to_base64(args.image)

    # Find ZIPs
    zip_files = [f for f in songs_dir.iterdir() if f.suffix.lower() == '.zip']
    print(f"📦 {len(zip_files)} ZIPs found")

    success = 0
    for zip_file in zip_files:
        try:
            # Extract song ID from filename
            song_id = zip_file.stem.split(' (')[0]
            song_folder = output_dir / Path(zip_file.stem)

            print(f"📤 {zip_file.name} → {song_folder.name}", end=" ")

            song_folder.mkdir(exist_ok=True)
            with ZipFile(zip_file, 'r') as z:
                z.extractall(song_folder)

            # Get hash
            map_hash = None
            if args.online:
                map_hash = get_map_hash_online(song_id)

            if not map_hash or args.local:
                map_hash = get_map_hash_local(song_folder)

            if map_hash:
                # Get song name from Info.dat
                info_path = song_folder / 'Info.dat'
                if not info_path.exists():
                    info_path = song_folder / 'info.dat'

                song_name = song_id
                if info_path.exists():
                    try:
                        with open(info_path, 'r', encoding='utf-8') as f:
                            info_data = json.load(f)
                            song_name = (info_data.get('_songName') or
                                         info_data.get('song', {}).get('title') or
                                         info_data.get('song', {}).get('name') or
                                         song_id)
                    except:
                        pass

                playlist["songs"].append({
                    "hash": map_hash,
                    "levelid": f"custom_level_{map_hash}",
                    "songName": song_name
                })
                success += 1
                print(f"✅ {map_hash[:8]}")
            else:
                print("❌ NO HASH")

        except Exception as e:
            print(f"❌ {e}")

    # Save
    output_file = output_dir / f"{args.name}.bplist"
    if args.dry_run:
        print(json.dumps(playlist, indent=2, ensure_ascii=False))
    else:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(playlist, f, indent=2, ensure_ascii=False)
        print(f"\n💾 {output_file}")

    print(f"✅ {success}/{len(zip_files)} OK")


if __name__ == "__main__":
    main()
