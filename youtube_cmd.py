# -*- coding: utf-8 -*-

# https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d
"""
Copyright (c) 2019 Valentin B.
A simple music bot written in discord.py using youtube-dl.
Though it's a simple example, music bots are complex and require much time and knowledge until they work perfectly.
Use this as an example or a base for your own bot and extend it as you want. If there are any bugs, please let me know.
Requirements:
Python 3.5+
pip install -U discord.py pynacl youtube-dl
You also need FFmpeg in your PATH environment variable or the FFmpeg.exe binary in your bot's directory on Windows.
"""
import re
import time
import asyncio
import functools
import itertools
import math
import random

from pytube import Playlist
import discord
import youtube_dl
from async_timeout import timeout
from discord.ext import commands
from parameter import music_help_str
# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -filter:a "loudnorm"',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing',
                               description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.source.duration)
                 .add_field(name='Requested by', value=self.requester.mention)
                 .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                 .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._loopqueue = False
        self._volume = 0.7
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def loopqueue(self):
        return self._loopqueue

    @loopqueue.setter
    def loopqueue(self, value: bool):
        self._loopqueue = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None
            # print(self.current.source)

            if self.loop:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
            else:
                # Try to get the next song within 3 minutes.
                    # If no song will be added to the queue in time,
                    # the player will disconnect due to performance
                    # reasons.
                if self.loopqueue:
                    source = await YTDLSource.create_source(self._ctx, self.current.source.url, loop=self.bot.loop)
                    song = Song(source)
                    await self.songs.put(song)
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())
            '''
            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())

            else:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
            '''

            await self.next.wait()

    def play_next_song(self, error=None):
        if error is not None:
            pass
            # raise VoiceError(str(error))
        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}
        self.counts = 0
        self.counts += 1
        self.timeout_check = {}
        self.guild_queue = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()
        # wait 180 sec, if do not call play, the robot will disconnect
        if ctx.guild.name in self.timeout_check:
            if self.timeout_check[ctx.guild.name]:
                return
        else:
            self.timeout_check[ctx.guild.name] = False
        for i in range(1, 36):
            await asyncio.sleep(5)
            if self.timeout_check[ctx.guild.name]:
                return

        await ctx.invoke(self._leave)


    @commands.command(name='summon')
    # @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect'])
    # @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        self.timeout_check.pop(ctx.guild.name, None)
        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int = -1):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if volume == -1:
            await ctx.send('Volume of the player set to {}%'.format(ctx.voice_state.volume*100))
            return

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing', 'NOW'])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause', aliases=['PAUSE'])
    # @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""

        if ctx.voice_state.voice.is_playing() : # and not ctx.voice_state.is_playing
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume', aliases=['RESUME'])
    # @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if ctx.voice_state.voice.is_paused(): #not ctx.voice_state.is_playing and
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop', aliases=['clear', 'STOP'])
    # @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.voice.is_playing(): # not ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip', aliases=['SKIP'])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(name='queue', aliases=['playlist', 'QUEUE'])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """
        # reference https://youtu.be/1KV5174e2Q0
        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')
        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page
        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        queue_message = await ctx.send(embed=embed)
        await queue_message.add_reaction('🔼')
        await queue_message.add_reaction('🔽')
        queue_message_start = time.time()
        queue_message_end = queue_message_start
        self.guild_queue[ctx.guild.name] = queue_message.id
        def check(reaction, user):
                    return user != queue_message.author and\
                    reaction.message.id == queue_message.id and \
                    (reaction.emoji == '🔼' or \
                    reaction.emoji == '🔽')
        while self.guild_queue[ctx.guild.name] == queue_message.id and queue_message_end - queue_message_start < 180:
            tasks = [
                asyncio.create_task(self.bot.wait_for(
                    "reaction_add", 
                    check=check,
                    timeout=180), name="radd"),
                asyncio.create_task(self.bot.wait_for(
                    "reaction_remove", 
                    check=check,
                    timeout=180), name="rremove"),
            ]
            done, pending = await asyncio.wait(tasks, return_when = asyncio.FIRST_COMPLETED)
            finished = list(done)[0]
            try:
                reaction, user = finished.result()
            except asyncio.TimeoutError:
                break
            for task in pending:
                try:
                    task.cancel()
                except asyncio.CancellError:
                    pass

            if reaction.emoji == '🔼':
                start = max(0, start - items_per_page)
                end = start + items_per_page
            elif reaction.emoji == '🔽':
                start = min((pages-1) * items_per_page, start + items_per_page)
                end = start + items_per_page
            else:
                continue
            queue = ''
            for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
                queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

            embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                     .set_footer(text='Viewing page {}/{}'.format(page, pages)))
            await queue_message.edit(embed=embed)
            queue_message_end = time.time()


    @commands.command(name='shuffle', aliases=['SHUFFLE'])
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove', aliases=['REMOVE'])
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop', aliases=['LOOP'])
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        if ctx.voice_state.loop:
            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❌')

    @commands.command(name='loopqueue', aliases=['LOOPQUEUE'])
    async def _loopqueue(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loopqueue = not ctx.voice_state.loopqueue
        if ctx.voice_state.loopqueue:
            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❌')

    @commands.command(name='play', aliases=['PLAY'])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        self.timeout_check[ctx.guild.name] = True
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)
        # check the link is playlist or not
        check_list = '(.*)youtube.com(.*)[&?]list=(.*)(&index=.*)?'
        check_result = re.search(check_list, search)
        if check_result is not None:
            play_list = 'https://www.youtube.com/playlist?list=' + check_result[3]
            pl = Playlist(play_list)  # get each website of video in play list
            if len(pl) == 0:
                await ctx.send('An error occurred while processing this request: {}'.format(str(search)))
            else:
                for link in pl:
                    try:
                        source = await YTDLSource.create_source(ctx, link, loop=self.bot.loop)
                    except YTDLError as e:
                        await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
                    else:
                        song = Song(source)
                        await ctx.voice_state.songs.put(song)

        else:
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except:
                await ctx.send('An error occurred while processing this request: {}'.format(str(search)))
                for i in range(1, 36):
                    await asyncio.sleep(5)
                    if ctx.voice_state.is_playing or len(ctx.voice_state.songs) > 0:
                        return

                await ctx.invoke(self._leave)
            else:
                song = Song(source)
                async with ctx.typing():
                    await ctx.voice_state.songs.put(song)
                    await ctx.send('Enqueued {}'.format(str(source)))


    @commands.command(name='test')
    async def _test(self, ctx: commands.Context):
        print(self.counts)
        self.counts += 1
    @commands.command(name='help_music')
    async def _helpmusic(self, ctx: commands.Context):
        await ctx.send(music_help_str)

    @_join.before_invoke
    @_play.before_invoke
    @_leave.before_invoke
    @_volume.before_invoke
    @_pause.before_invoke
    @_resume.before_invoke
    @_stop.before_invoke
    @_skip.before_invoke
    @_shuffle.before_invoke
    @_remove.before_invoke
    @_loop.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')
            # await ctx.reply('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('You are not in the same voice channel as the bot.')


