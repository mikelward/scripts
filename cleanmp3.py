#!/usr/bin/python

import os
import mutagen

musicroot = r'''/home/mikel/allmusic/iTunes/iTunes Music'''

# whitelist of tracks I legitimately own/are free
free = {}
free['genre'] = [u'Podcast']
free['album'] = [u'Bioshock',                     # Bioshock game soundtrack - free download
                 u'FLOSS Weekly',                 # FLOSS Weekly podcast - missing genre
                 u'Speakerboxxx/The Love Below'   # has silent tracks that I deleted
                 ]

def is_free(track):
    for attribute in free:
        if attribute in track:
            for track_attribute in track[attribute]:
                if track_attribute in free[attribute]:
                    return True
    return False

def is_purchased(track, path):
    '''Return True if we can determine that file was purchased from the iTunes store, False otherwise.
    
    Note that False doesn't guarantee the file was not purchased,
    for example it could use a different format, or have been ripped from a purchased CD.'''
    if hasattr(track, 'MP4Tags'):
        try:
            mp4 = mutagen.mp4.Open(path)
            # 'purd' is the purchase date
            if 'purd' in mp4:
                return mp4['purd'] != None
            else:
                return False
        except:
            return False

def print_track(track, path):
    title = track.get('title', [u'Unknown'])[0]
    artist = track.get('artist', [u'Unknown'])[0]
    album = track.get('album', [u'Unknown'])[0]
    genre = track.get('genre', [u'Unknown'])[0]
    encoder = track.get('encodedby', [u'Unknown'])[0]
    free_str = 'yes' if is_free(track) else 'no'
    print '{0}: title={1} artist={2} album={3} genre={4} free={5}'.format(
            path, title, artist, album, genre, free_str)

def to_int(tracknum):
    value = 0
    for c in tracknum:
        if c.isdigit():
            value = value * 10 + int(c)
        else:
            return value
    return value

def dirs_to_check(musicdir, musicroot):
    album_tracks = {}

    for file in os.listdir(musicdir):
        path = os.path.join(musicdir, file)
        if os.path.isfile(path):
            try:
                track = mutagen.File(path, easy=True)
            except:
                track = None
            if track:
                if is_free(track): continue
                if is_purchased(track, path): continue

                #print track
                #print_track(track, path)
                album = track.get('album', [u'Unknown'])[0]
                if album == u'Unknown':
                    print '{0}: no album name'.format(path)
                    continue

                tracknumber = track.get('tracknumber', [u'Unknown'])[0]
                #print 'tracknumber={0}'.format(tracknumber)
                tracknumber = to_int(tracknumber)
                if tracknumber == 0:
                    print '{0}: no track number'.format(path)
                    continue

                if album not in album_tracks:
                    album_tracks[album] = []
                album_tracks[album].append(tracknumber)
        elif os.path.isdir(path):
            dirs_to_check(path, musicroot)

    for album in album_tracks:
        tracks = album_tracks[album]
        tracks.sort()
        ntracks = len(tracks)
        maxtrack = tracks[-1]
        if ntracks != maxtrack:
            print '{0}: bad number of tracks (last={1}, tracks={2})'.format(mp3dir, maxtrack, ntracks)
            continue
        for i in range(1, tracks[-1]):
            if tracks[i-1] != i:
                print '{0}: missing track {1}'.format(mp3dir, i)
                break

dirs_to_check(musicdir, musicroot)

