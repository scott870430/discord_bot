import re
import discord
import pandas as pd
import pygsheets
import time
import calendar
from datetime import datetime, timedelta
import asyncio
from discord.ext import commands
from parameter import *


class Pc_bot(commands.Cog):
    def __init__(self, bot: commands.Bot, url, authorize_file):
        self.bot = bot
        gc = pygsheets.authorize(service_file=authorize_file)
        self.sht = gc.open_by_url(url)
        self.url = url
        self.id2member = None
        self.index2id = None # (index, name)
        self.get_member_sheet()
        self.data = self.check_day()
        self.remain = self.bot.loop.create_task(self.auto_remain())

    def get_member_sheet(self):
        member_sheet = self.sht.worksheet_by_title(MEMBER_SHEET_NAME)
        df = pd.DataFrame(member_sheet.get_all_records())
        self.id2member = dict([(i, [e, a]) for e, (i, a) in enumerate(zip(df.loc[:, "discord_id"], df.loc[:, "member"]))])
        self.index2id = dict([(e, i) for e, i in enumerate(df.loc[:, "discord_id"])])


    def check_day(self):
        today = datetime.today()
        hour = int(today.strftime("%H"))
        if hour > 5:
            self.data = today.strftime("%m/%d")
        else:
            yday= datetime.today() - timedelta(days=1)
            self.data = yday.strftime("%m/%d")

    def get_member(self, idx):
        if idx not in self.id2member:
            return None, None
        return self.id2member[idx] # (index, name)

    def check_boss(self, boss_hit):
        if boss_hit in BOSS_ONE:
            return BOSS[1]
        elif boss_hit in BOSS_TWO:
            return BOSS[2]
        elif boss_hit in BOSS_THREE:
            return BOSS[3]
        elif boss_hit in BOSS_FOUR:
            return BOSS[4]
        elif boss_hit in BOSS_FIVE:
            return BOSS[5]
        else:
            return None
    def get_sheet(self):
        try:
            clan_hit_sheet = self.sht.worksheet_by_title(self.data)
        except pygsheets.WorksheetNotFound:
            return None
        df = pd.DataFrame(clan_hit_sheet.get_all_records())
        return df
    def create_hit_info(self, who, damage, boss, fill_status, is_rehit):
	    embed = (discord.Embed(title='報刀情況',
	                               color=discord.Color.blurple())
	                 .add_field(name='出刀人', value=who)
	                 .add_field(name='傷害', value='{}w'.format(damage))
	                 .add_field(name='Boss', value=boss)
                     .add_field(name='殘刀', value=is_rehit)
                     .add_field(name='填表', value=fill_status))

	    return embed

    @commands.command(name='status')
    async def _status(self, ctx, _id=None):
        self.check_day()
        df = self.get_sheet()
        if df is None:
            await ctx.send("ERROR! SHEET {} 未找到".format(self.data))
            return
        if _id is None:
            names = ''
            hits = ''
            for e in df.loc[:, "名稱"]:
                names += '{}\n'.format(e)
            for e in df.loc[:, "剩餘刀數"]:
                hits += '  {}\n'.format(e)

            embed = (discord.Embed(title='status',
                                       color=discord.Color.blurple())
                         .add_field(name='名稱', value=names)
                         .add_field(name='剩餘刀數', value=hits))

            await ctx.send(embed=embed)
        else:
            _id = re.search(CHECK_ID, _id)
            if _id is None:
                await ctx.reply("ERROR! 請標記成員")
            idx, name = self.get_member(int(_id[1]))
            info = df.iloc[idx+1]
            embed = (discord.Embed(title='{} status'.format(name),
                                       color=discord.Color.blurple())
                         .add_field(name='剩餘刀數', value=info['剩餘刀數'])
                         .add_field(name='閃退', value=info['閃退'], inline=False)
                         .add_field(name='第一刀', value=info['第一隊'] if info['第一隊'] !='' else '未出')
                         .add_field(name='第二刀', value=info['第二隊'] if info['第二隊'] !='' else '未出')
                         .add_field(name='第三刀', value=info['第三隊'] if info['第三隊'] !='' else '未出')
                         )
            await ctx.send(embed=embed)

    @commands.command(name='create_sheet')
    async def _create_sheet(self, ctx):
        month = int(datetime.today().strftime('%m'))
        year = int(datetime.today().strftime('%Y'))
        weekday, count_day = calendar.monthrange(year=year, month=month)
        template = self.sht.worksheet_by_title('template')
        for i in range(5, 0, -1):
            last_day = datetime(year=year, month=month, day=count_day - (i-1))
            name = last_day.strftime('%m/%d')
            try:
                temp = self.sht.worksheet_by_title(name)
            except: 
                self.sht.add_worksheet(title=name, src_worksheet=template)

        await ctx.message.reply("創建完成!")

    def check_last_5days(self):
        month = int(datetime.today().strftime('%m'))
        year = int(datetime.today().strftime('%Y'))
        today_date = datetime.today().strftime('%m/%d')
        weekday, count_day = calendar.monthrange(year=year, month=month)

        for i in range(5, 0, -1):
            last_day = datetime(year=year, month=month, day=count_day - (i-1))
            l = last_day.strftime('%m/%d')
            if today_date == l and i == 1:
                return True, True
            if today_date == l:
                return True, False
        return False, False
        

    @commands.command(name='url')
    async def _url(self, ctx):
        await ctx.send(self.url)

    async def _check_last_hit(self, ctx, idx, is_rehit):
        try:
            clan_hit_sheet = self.sht.worksheet_by_title(self.data)
        except pygsheets.WorksheetNotFound:
            await ctx.send("ERROR! SHEET {} 未找到".format(self.data))
            return None
        if not is_rehit:
            last_hit = clan_hit_sheet.get_value((idx + HIT_TOP_COLUMN_NUM,
                LAST_HIT_COLUMN_NUM))
            return last_hit
        else:
            for i in range(3):
                cell_value = clan_hit_sheet.get_value((idx + HIT_TOP_COLUMN_NUM,
                    REHIT_DAMAGE_COLUMN[i]))
                if cell_value == '':
                    return TOTAL_HIT_NUM - i
            return 0


    @commands.command(name='fill', aliases=['FILL', 'Fill'])
    async def _fill(self, ctx: commands.Context):
        self.check_day()
        msg = ctx.message.content.split()
        if len(msg) < 3:
            await ctx.message.reply('格式錯誤!')
            return
        is_rehit = False
        check_result = re.search(CHECK_ID, msg[1])
        if check_result is not None:
            idx, name = self.get_member(int(check_result[1]))
            if idx is None and name is None:
                await ctx.message.reply('查無此戰隊成員!')
                return
            damage = msg[2]
            boss_hit = msg[3]
            if len(msg) == 5:
                rehit_result = re.search(CHECK_REHIT, msg[4])
                if rehit_result is not None:
                    is_rehit = True
        else:
            idx, name = self.get_member(ctx.message.author.id)
            damage = msg[1]
            boss_hit = msg[2]
            if len(msg) == 4:
                rehit_result = re.search(CHECK_REHIT, msg[3])
                if rehit_result is not None:
                    is_rehit = True

        damage_check = '(\d*)[w萬]?'
        damage_result = re.search(damage_check, damage)
        if damage_result is None:
            await ctx.message.reply('傷害格式錯誤')
        else:
            damage = damage_result[1]
        
        boss_name = self.check_boss(boss_hit)
        if boss_name is None:
            await ctx.message.reply('目標錯誤')
            return

        last_hit = await self._check_last_hit(ctx, idx, is_rehit)
        if last_hit is None:
            return 

        count = TOTAL_HIT_NUM - int(last_hit) 
        if count > 2:
            await ctx.message.reply('你已經出三刀啦!')
            return 

        embed = self.create_hit_info(name, damage, boss_name, NOT_FILL, is_rehit)
        info_message = await ctx.send(embed=embed)
        await info_message.add_reaction(CORRECT_EMOJI)
        await info_message.add_reaction(ERROR_EMOJI)

        fill_message_start = time.time()
        fill_message_end = fill_message_start

        while fill_message_end - fill_message_start < 60:
            try:
                def check(reaction, user):
                    return user == ctx.message.author and \
                    reaction.message.id == info_message.id and \
                    (reaction.emoji == CORRECT_EMOJI or \
                    reaction.emoji == ERROR_EMOJI)
                
                reaction, user = await self.bot.wait_for(
                        "reaction_add", 
                        check=check,
                        timeout=60)
            except asyncio.TimeoutError:
                fill_message_end = time.time()
                break

            if reaction.emoji == CORRECT_EMOJI:
                break
            elif reaction.emoji == ERROR_EMOJI:
                await info_message.delete()
                await ctx.message.reply('取消填刀!')
                return

        clan_hit_sheet = self.sht.worksheet_by_title(self.data)
        last_hit = await self._check_last_hit(ctx, idx, is_rehit)
        count = TOTAL_HIT_NUM - int(last_hit) 
        if count > 2:
            await ctx.message.reply('你已經出三刀啦!')
            return 
        else:
            if is_rehit:
                clan_hit_sheet.update_value(
                        (idx + HIT_TOP_COLUMN_NUM, REHIT_DAMAGE_COLUMN[count]), int(damage)*10000)
                clan_hit_sheet.update_value(
                        (idx + HIT_TOP_COLUMN_NUM, REHIT_BOSS_COLUMN[count]), boss_name)
            else:
                clan_hit_sheet.update_value(
                        (idx + HIT_TOP_COLUMN_NUM, DAMAGE_COLUMN[count]), int(damage)*10000)
                clan_hit_sheet.update_value(
                        (idx + HIT_TOP_COLUMN_NUM, BOSS_COLUMN[count]), boss_name)
            embed = self.create_hit_info(name, damage, boss_name, IS_FILL, is_rehit)
            await info_message.edit(embed=embed)
            await info_message.remove_reaction(ERROR_EMOJI, member=info_message.author)

            last_hit = clan_hit_sheet.get_value((3, 6))

    @commands.command(name='登記閃退', aliases=['閃退'])
    async def _slip(self, ctx, _id=None):
        if _id is None:
            idx, name = self.get_member(ctx.message.author.id)
        else:
            _id = re.search(CHECK_ID, _id)
            if _id is None:
                await ctx.reply("ERROR! 請標記成員")
            idx, name = self.get_member(int(_id[1]))
        self.check_day()
        clan_hit_sheet = self.sht.worksheet_by_title(self.data)
        clan_hit_sheet.update_value((idx + HIT_TOP_COLUMN_NUM, SLIP), True)
        await ctx.message.add_reaction(CORRECT_EMOJI)

    @commands.command(name='help_pc')
    async def _help_pc(self, ctx: commands.Context):
        await ctx.send(pc_help_str)


    async def auto_remain(self):
        await self.bot.wait_until_ready()
        self.REMAIN_CHANNEL = self.bot.get_channel(REMAIN_CHANNEL)
        reamin_hour = REMAIN_HOUR
        sent = False
        while True:
            today = datetime.today()
            hour = int(today.strftime("%H"))
            if reamin_hour == hour:
                last_5, last_1 = self.check_last_5days()
                if not sent and last_5:
                    self.check_day()
                    df = self.get_sheet()
                    if df is None:
                        pass
                    else:
                        remain_string = ''
                        for i, e in enumerate(df.loc[:, "剩餘刀數"][1:]):
                            if i > 29:
                                break
                            if int(e) > 0:
                                remain_string += "<@{}> ".format(self.index2id[i])
                        await self.REMAIN_CHANNEL.send(remain_string + REMAIN_STR)
                        sent = True
            else:
                sent = False
            await asyncio.sleep(3600)